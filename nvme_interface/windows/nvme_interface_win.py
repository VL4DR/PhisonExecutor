import time
import ctypes
from ctypes import wintypes
from ctypes import windll
from common import nvme_common
from common import exceptions
import nvme_interface.windows.nvme_interface_win_defs as win_nvme

class NVMEInterface:
    """Windows-based NVMe communication interface.
	"""
    def __init__(self, device_path : str):
        self._device = NVMEInterface._open_device(device_path)
        self._device_path = device_path
        self._method = win_nvme.IoctlMethod.IOCTL_METHOD_SCSI_PASSTHROUGH_DIRECT

		# @todo some drives only work with StorageProtocol, see if we can support this somehow.
        #self._method = win_nvme.IoctlMethod.IOCTL_METHOD_NVME_STORAGE_PROTOCOL

    @staticmethod
    def _open_device(device_path : str) -> wintypes.HANDLE:
        """Open a device.

        :param device_path: Path to device.
        :type device_path: str
        :raises exceptions.DeviceInaccessibleException: Device could not be opened.
        :return: Handle to opened device.
        :rtype: wintypes.HANDLE
        """
        handle = wintypes.HANDLE(win_nvme.CreateFileA(device_path.encode('utf-8'),
								win_nvme.GENERIC_READ | win_nvme.GENERIC_WRITE,
								win_nvme.FILE_SHARE_READ | win_nvme.FILE_SHARE_WRITE,
								0,
								win_nvme.OPEN_EXISTING,
								win_nvme.FILE_ATTRIBUTE_NORMAL,
								0))
        if handle is None or handle.value == wintypes.HANDLE(win_nvme.INVALID_HANDLE_VALUE):
            raise exceptions.DeviceInaccessibleException("Could not open the requested device!")

        return handle


    @staticmethod
    def _build_cdb(operation : win_nvme.CDBOperation, data_transfer_length : int)\
        -> win_nvme.SCSICDBData:
        """Build a CDB structure to send over SCSI.

        :param operation: CDB operation.
        :type operation: win_nvme.CDBOperation
        :param data_transfer_length: Data transfer length.
        :type data_transfer_length: int
        :return: The populated CDB
        :rtype: win_nvme.SCSICDBData
        """
        cdb = win_nvme.SCSICDBData()

        data_transfer_length_be = int.from_bytes(
            int.to_bytes(data_transfer_length, 4, 'little'), 'big')
        if operation == win_nvme.CDBOperation.SCSI_SEND_SQ:
            cdb.main_code = win_nvme.CDB_CODE_SEND_SQ
            cdb.sub_code = win_nvme.CDB_SUB_CODE_SEND_SQ
        elif operation == win_nvme.CDBOperation.SCSI_TRIGGER:
            cdb.main_code = win_nvme.CDB_CODE_TRIGGER_WRITE
            cdb.sub_code = win_nvme.CDB_SUB_CODE_TRIGGER
        elif operation == win_nvme.CDBOperation.SCSI_WRITE_DATA:
            cdb.main_code = win_nvme.CDB_CODE_TRIGGER_WRITE
            cdb.sub_code = data_transfer_length_be
        else:
            # win_nvme.CDBOperation.SCSI_READ_DATA
            cdb.main_code = win_nvme.CDB_CODE_READ
            cdb.sub_code = data_transfer_length_be

        return cdb

    @staticmethod
    def _build_nvme_request(opcode : int, nsid : int, **kwargs : dict)\
        -> tuple[win_nvme.NVMECmd, bytes, int]:
        """Build an NVMe request structure.

        :param opcode: NVMe command code.
        :type opcode: int
        :param nsid: Namespace ID.
        :type nsid: int
        :raises ValueError: data was provided, but data length was not.
        :raises ValueError: data length is invalid.
        :raises ValueError: Invalid combination of data and data length.
        :return: The NVMe request structure along with the data to be sent with the data length.
        :rtype: tuple[win_nvme.NVMECmd, bytes, int]
        """
        nvme_cmd = win_nvme.NVMECmd()
        nvme_cmd.opcode = opcode
        nvme_cmd.nsid = nsid

        actual_data_len = 0
        actual_data = b''

        if 'data' in kwargs and 'data_len' not in kwargs:
            raise ValueError("If 'data' is provided, then 'data_len' must also be provided")

        if 'cdw10' in kwargs:
            nvme_cmd.cdw10 = kwargs['cdw10']
        if 'cdw11' in kwargs:
            nvme_cmd.cdw11 = kwargs['cdw11']
        if 'cdw12' in kwargs:
            nvme_cmd.cdw12 = kwargs['cdw12']
        if 'cdw13' in kwargs:
            nvme_cmd.cdw13 = kwargs['cdw13']
        if 'cdw14' in kwargs:
            nvme_cmd.cdw14 = kwargs['cdw14']
        if 'cdw15' in kwargs:
            nvme_cmd.cdw15 = kwargs['cdw15']
        if 'data_len' in kwargs:
            data_len = kwargs['data_len']
            if data_len < 0 or data_len > nvme_common.NVME_MAX_TRANSFER_SIZE:
                raise ValueError("Invalid length provided!")
            actual_data_len = data_len
            if actual_data_len != 0:
                if 'data' in kwargs:
                    if len(kwargs['data']) < data_len:
                        raise ValueError("Invalid combination of 'data' and 'data_len'!")
                    actual_data = kwargs['data']

        return nvme_cmd, actual_data, actual_data_len


    def _execute_ioctl(self, ioctl_code : int, in_buffer : bytes) -> bytes:
        """Execute an IOControl operation.

        :param ioctl_code: IOControl operation code.
        :type ioctl_code: int
        :param in_buffer: Input buffer to include in the ioctl.
        :type in_buffer: bytes
        :return: The data returned from the ioctl.
        :rtype: bytes
        """
        DeviceIoControl = windll.kernel32.DeviceIoControl
        DeviceIoControl.argtypes = [
				wintypes.HANDLE,
				wintypes.DWORD,
				wintypes.LPVOID,
				wintypes.DWORD,
				wintypes.LPVOID,
				wintypes.DWORD,
				ctypes.POINTER(wintypes.DWORD),
				wintypes.LPVOID]
        DeviceIoControl.restype = wintypes.BOOL

        bytes_returned = wintypes.DWORD(0)

        ioctl_data_buffer = (len(in_buffer) * ctypes.c_ubyte).from_buffer_copy(in_buffer)
        ret = DeviceIoControl(self._device,
					ioctl_code,
					ioctl_data_buffer,
					len(ioctl_data_buffer),
					ioctl_data_buffer,
					len(ioctl_data_buffer),
					ctypes.pointer(bytes_returned),
					0)

        if ret == 0:
            raise RuntimeError(f"Ioctl failed! {windll.kernel32.GetLastError()}")

        return bytes(ioctl_data_buffer)

    def _send_scsi_passthrough(self,
                               direction : win_nvme.DataDirection,
                               in_buffer : bytes, transfer_size : int,
                               cdb : win_nvme.SCSICDBData) -> bytes:
        """Issue Passthrough SCSI request.

        :param direction: Operation direction.
        :type direction: win_nvme.DataDirection
        :param in_buffer: Data to send.
        :type in_buffer: bytes
        :param transfer_size: Transfer size.
        :type transfer_size: int
        :param cdb: CDB structure
        :type cdb: win_nvme.SCSICDBData
        :raises RuntimeError: Unexpected SCSI status code.
        :return: Returned data from SCSI request.
        :rtype: bytes
        """
        cdb_bytes = bytes(cdb)

        scsi_passthrough = win_nvme.SCSIPassThroughDirect()
        scsi_passthrough.length = ctypes.sizeof(win_nvme.SCSIPassThroughDirect)
        scsi_passthrough.cdb_length = win_nvme.SCSI_CDB_LENGTH
        scsi_passthrough.timeout = nvme_common.NVME_STANDARD_TIMEOUT_SECONDS
        scsi_passthrough.cdb = (len(cdb_bytes) * ctypes.c_ubyte).from_buffer_copy(bytes(cdb_bytes))
        scsi_passthrough.data_in = direction.value
        scsi_passthrough.data_transfer_length = transfer_size

        data_buffer = (transfer_size * ctypes.c_ubyte)()

        if transfer_size > 0:
            if direction == win_nvme.DataDirection.DIRECTION_OUT:
                assert not in_buffer is None and len(in_buffer) >= transfer_size
                data_buffer = (transfer_size * ctypes.c_ubyte).from_buffer_copy(in_buffer)

        scsi_passthrough.data_buffer = ctypes.cast(data_buffer, wintypes.LPVOID)

        out_buffer = self._execute_ioctl(
            win_nvme.IOCTL_SCSI_PASSTHROUGH_DIRECT, bytes(scsi_passthrough))
        out_scsi_data = win_nvme.SCSIPassThroughDirect.from_buffer_copy(out_buffer)
        if out_scsi_data.scsi_status != 0:
            raise RuntimeError(f"SCSI Status: {out_scsi_data.scsi_status}")

        data_buffer = (len(data_buffer) * ctypes.c_ubyte).from_address(scsi_passthrough.data_buffer)
        return bytes(data_buffer)

    def _send_nvme_over_scsi(self,
                             nvme_cmd : win_nvme.NVMECmd,
                             actual_data : bytes,
                             actual_data_len : int) -> tuple[int, bytes]:
        """Send an NVMe request over SCSI.

        :param nvme_cmd: The NVMe request.
        :type nvme_cmd: win_nvme.NVMECmd
        :param actual_data: data to include in the NVMe request.
        :type actual_data: bytes
        :param actual_data_len: Data length.
        :type actual_data_len: int
        :return: A tuple of the NVMe status code and the returned data bytes.
        :rtype: tuple[int, bytes]
        """
        direction = win_nvme.DataDirection.DIRECTION_OUT
        cdb_type = win_nvme.CDBOperation.SCSI_WRITE_DATA

        if len(actual_data) == 0 and actual_data_len > 0:
            direction = win_nvme.DataDirection.DIRECTION_IN
            cdb_type = win_nvme.CDBOperation.SCSI_READ_DATA
        elif len(actual_data) == 0 and actual_data_len == 0:
            cdb_type = win_nvme.CDBOperation.SCSI_TRIGGER
            actual_data_len = win_nvme.SCSI_TRIGGER_BUFFER_LENGTH
            actual_data = b"\x00" * actual_data_len

        curr_cdb = NVMEInterface._build_cdb(
            win_nvme.CDBOperation.SCSI_SEND_SQ, ctypes.sizeof(nvme_cmd))
        self._send_scsi_passthrough(win_nvme.DataDirection.DIRECTION_OUT,
                                    bytes(nvme_cmd), ctypes.sizeof(nvme_cmd),
                                    curr_cdb)

        curr_cdb = NVMEInterface._build_cdb(cdb_type, actual_data_len)
        # @todo fix the error code here.
        return 0, self._send_scsi_passthrough(direction, actual_data, actual_data_len, curr_cdb)

    def _send_nvme_over_storage_protocol(self,
                                         nvme_cmd : win_nvme.NVMECmd,
                                         actual_data : bytes,
                                         actual_data_len : int) -> tuple[int, bytes]:
        """Send an NVMe request over Storage Protocol.

        :param nvme_cmd: The NVMe request
        :type nvme_cmd: win_nvme.NVMECmd
        :param actual_data: data to include in the NVMe request.
        :type actual_data: bytes
        :param actual_data_len: Data length.
        :type actual_data_len: int
        :raises RuntimeError: Unexpected Storage Protocol status returned.
        :return: A tuple of the NVMe status code and the returned data bytes.
        :rtype: tuple[int, bytes]
        """
        protocol_command = win_nvme.StorageProtocolCommand()
        protocol_command.version = win_nvme.STORAGE_PROTOCOL_STRUCTURE_VERSION
        protocol_command.length = ctypes.sizeof(protocol_command)
        protocol_command.protocol_type = win_nvme.PROTOCOL_TYPE_NVME
        protocol_command.flags = win_nvme.STORAGE_PROTOCOL_COMMAND_FLAG_ADAPTER_REQUEST
        protocol_command.command_length = ctypes.sizeof(win_nvme.NVMECmd)
        protocol_command.timeout = nvme_common.NVME_STANDARD_TIMEOUT_SECONDS
        protocol_command.command_specific = win_nvme.STORAGE_PROTOCOL_SPECIFIC_NVME_ADMIN_COMMAND

        nvme_cmd_bytes = bytearray(nvme_cmd)
        protocol_command.command = nvme_cmd_bytes[0]

        # The struct is padded such that it's aligned to 4...
        data_tail = nvme_cmd_bytes[4 : ]

        # Request data from the controller
        if len(actual_data) == 0 and actual_data_len > 0:
            protocol_command.data_from_device_transfer_length = actual_data_len
            protocol_command.data_from_device_buffer_offset = \
                ctypes.sizeof(win_nvme.StorageProtocolCommand) + ctypes.sizeof(win_nvme.NVMECmd) - 4
            data_tail += b'\x00' * actual_data_len
        # Send data to controller
        elif len(actual_data) > 0:
            protocol_command.data_to_device_transfer_length = actual_data_len
            protocol_command.data_to_device_buffer_offset = \
                ctypes.sizeof(win_nvme.StorageProtocolCommand) + ctypes.sizeof(win_nvme.NVMECmd) - 4
            data_tail += actual_data[ : actual_data_len]

        returned_data_buffer = self._execute_ioctl(
            win_nvme.IOCTL_STORAGE_PROTOCOL_COMMAND, bytes(protocol_command) + data_tail)
        storage_protocol_response = win_nvme.StorageProtocolCommand.from_buffer_copy(
            returned_data_buffer)
        if storage_protocol_response.return_status != win_nvme.STORAGE_PROTOCOL_STATUS_SUCCESS:
            raise RuntimeError(
                f"Controller returned status {hex(storage_protocol_response.return_status)}")

        offset_to_data = ctypes.sizeof(
            win_nvme.StorageProtocolCommand) + ctypes.sizeof(win_nvme.NVMECmd) - 4
        transfer_length = storage_protocol_response.data_from_device_transfer_length

		# @todo fix the error code here.
        return 0, bytes(returned_data_buffer)[offset_to_data : offset_to_data + transfer_length]

    def nvme_send_command(self, opcode : int, nsid : int, **kwargs : dict):
        """Send an NVMe command to the controller.

		:param opcode: NVMe command code.
		:type opcode: int
		:param nsid: Namespace ID.
		:type nsid: int
		:raises ValueError: Invalid method provided.
		:return: The ioctl return code and the NVMe buffer contents.
		:rtype: tuple[int, bytes]
		"""
        nvme_cmd, actual_data, actual_data_len = self._build_nvme_request(opcode, nsid, **kwargs)

        if self._method == win_nvme.IoctlMethod.IOCTL_METHOD_NVME_STORAGE_PROTOCOL:
            return self._send_nvme_over_storage_protocol(nvme_cmd, actual_data, actual_data_len)
        if self._method == win_nvme.IoctlMethod.IOCTL_METHOD_SCSI_PASSTHROUGH_DIRECT:
            return self._send_nvme_over_scsi(nvme_cmd, actual_data, actual_data_len)
        raise ValueError("Invalid method!")
