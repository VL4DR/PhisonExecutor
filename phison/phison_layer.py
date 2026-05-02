import ctypes
try:
    import nvme_interface.linux.nvme_interface_linux as nvme_interface
except ImportError:
    import nvme_interface.windows.nvme_interface_win as nvme_interface
from common import nvme_common
import phison.phison_defs as phison

def phison_vsc(func):
    def vsc_wrapper(self, *args, **kwargs):
        self.unlock_vsc()
        return func(self, *args, **kwargs)
    return vsc_wrapper


class PhisonLayer:
    """Phison VSC command layer.
	"""
    def __init__(self, device_path : str):
        self._nvme = nvme_interface.NVMEInterface(device_path)

    @staticmethod
    def _calculate_crc(buf : bytes) -> int:
        """Compute CRC on a byte buffer.

		:param buf: _description_
		:type buf: bytes
		:return: The CRC refsult.
		:rtype: int
		"""
        crc = 0
        for elem in buf:
            shifted = elem << 8
            for _ in range(8):
                curr = 0x1021 ^ (crc << 1)

                if ((shifted ^ crc) & 0x8000) == 0:
                    curr = crc << 1

                shifted <<= 1
                crc = curr

        return ((crc & 0xFF) << 8) | ((crc >> 8) & 0xFF)


    @staticmethod
    def _calculate_request_crc(crc_data : phison.PhisonCRCData) -> int:
        """Calculate the Phison VSC request CRC.

		:param crc_data: The data to compute CRC for.
		:type crc_data: phison.PhisonCRCData
		:return: The CRC result.
		:rtype: int
		"""
        crc_data.cdw11 = 0
        crc_data.cdw15 &= 0xFFFF

        result = PhisonLayer._calculate_crc(bytes(crc_data))

        return result


    def _send_phison_vsc(self, opcode : phison.PhisonVSCCmd, nsid : int, **kwargs : dict) -> bytes:
        """Send a Phison VSC command.

		:param opcode: The Phison VSC command code.
		:type opcode: phison.PhisonVSCCmd
		:param nsid: Namespace ID.
		:type nsid: int
		:return: NVMe buffer data.
		:rtype: bytes
		"""
        crc_data = phison.PhisonCRCData()
        crc_data.opcode = opcode.value

        if 'cdw10' in kwargs:
            crc_data.cdw10 = kwargs['cdw10']
        if 'cdw11' in kwargs:
            crc_data.cdw11 = kwargs['cdw11']
        if 'cdw12' in kwargs:
            crc_data.cdw12 = kwargs['cdw12']
        if 'cdw13' in kwargs:
            crc_data.cdw13 = kwargs['cdw13']
        if 'cdw14' in kwargs:
            crc_data.cdw14 = kwargs['cdw14']
        if 'cdw15' in kwargs:
            crc_data.cdw15 = kwargs['cdw15']

        request_crc = PhisonLayer._calculate_request_crc(crc_data)

        if 'cdw15' in kwargs:
            kwargs['cdw15'] = (request_crc << 16) | (kwargs['cdw15'] & 0xFFFF)
        else:
            kwargs['cdw15'] = request_crc << 16

        return self._nvme.nvme_send_command(opcode.value, nsid, **kwargs)

    def _do_security_receive(self,
                             major : phison.PhisonSecuritySendReceiveMajorCommand,
                             minor : phison.PhisonSecuritySendReceiveMinorCommand,
                             size : int) -> bytes:
        """Issue an NVM Security Receive command based on Phison's command codes.
        
        :param major: The major command code.
        :type major: phison.PhisonSecuritySendReceiveMajorCommand
        :param minor: The minor command code.
        :type minor: phison.PhisonSecuritySendReceiveMinorCommand
        :param size: The receive size in bytes.
        :type size: int
        :return: Security Receive data.
        :rtype: bytes
        """
        assert size > 0

        security_receive_args = {'cdw10' : major.value << 24 | minor.value << 8,
                                 'cdw11' : size,
                                 'data_len' : size}

        return self._nvme.nvme_send_command(nvme_common.NVMEOpcode.NVME_SECURITY_RECEIVE.value,
                                            0,
                                            **security_receive_args)


    @phison_vsc
    def _phison_fw_download_chunk(self, offset : int, chunk_data : bytes):
        """Send a Phison VSC command.

		:param chunk_data: The Phison VSC command code.
		:type chunk_data: phison.PhisonVSCCmd
        :raises phison.PhisonVSCFailedException: Error in VSC processing of a chunk.
        :raises ValueError: offset is negative.
        :raises ValueError: length of chunk is invalid.

        .note :: length of chunk data must be >= 4 and <= nvme_common.NVME_MAX_TRANSFER_SIZE.
        """
        assert offset >= 0
        chunk_size = len(chunk_data)
        assert chunk_size >= 4 and chunk_size <= nvme_common.NVME_MAX_TRANSFER_SIZE

        download_args = {'cdw10' : chunk_size >> 2,
                         'cdw12' : (nvme_common.NVMEOpcode.NVME_FW_DOWNLOAD.value << 8) |\
                            phison.PhisonVSCSubCmd.PHISON_VSC_EXECUTE_STANDARD.value,
                            'cdw14' : offset >> 2,
                            'data' : chunk_data,
                            'data_len' : chunk_size}

        ioctl_ret, _ = self._send_phison_vsc(
                phison.PhisonVSCCmd.PHISON_SEND, 0, **download_args)
        if ioctl_ret != 0:
            raise phison.PhisonVSCFailedException(
                f"Chunk at offset {offset}, could not be downloaded.\
                    Error code {hex(ioctl_ret)}")

    def unlock_vsc(self):
        """Unlock processing of the next VSC command.

		:raises phison.PhisonVSCFailedException: Failure unlocking VSC.
		"""
        unlock_vsc_args = {'cdw13' : phison.VSC_UNLOCK_MAGIC}

        ret_code, _ = self._send_phison_vsc(
            phison.PhisonVSCCmd.PHISON_CONFIGURE, 0, **unlock_vsc_args)
        if ret_code != 0:
            raise phison.PhisonVSCFailedException(
                f"Unlocking VSC failed. Error code {hex(ret_code)}")


    @phison_vsc
    def phison_get_vsc_log_page(self,
                                vsc_log_page_id : phison.PhisonVSCLogPageId,
                                offset : int,
                                size : int,
                                use_security_receive : bool = False):
        """Get Phison VSC log page data.

        :param vsc_log_page_id: The log page ID to get data from.
        :type vsc_log_page_id: phison.PhisonVSCLogPageId
        :param offset: the offset, in bytes, within the target log page.
        :type offset: int
        :param size: the size, in bytes, of data to read from log page.
            Must be aligned to 4.
        :type size: int
        :raises ValueError: Size to read is non-positive, not aligned to 4 or too big.
        :raises ValueError: Offset is negative or too big.
        :return: Log page data.
        :rtype: bytes
        """
        if size % 4 != 0 or size <= 0 or size > nvme_common.NVME_MAX_TRANSFER_SIZE:
            raise ValueError(f"Size {hex(size)} is invalid!")

        if offset < 0 or offset >= 2 ** 23:
            raise ValueError(f"Offset {hex(offset)} is invalid!")

        read_log_page_args = {'cdw10' : size >> 2,
                              'cdw12' : (nvme_common.NVMEOpcode.NVME_GET_LOG_PAGE.value << 8) |\
                              phison.PhisonVSCSubCmd.PHISON_VSC_EXECUTE_STANDARD.value,
                              'cdw13' : vsc_log_page_id.value,
                              'cdw14' : offset << 9,
                              'data_len' : size}

        ioctl_ret, log_data = self._send_phison_vsc(
            phison.PhisonVSCCmd.PHISON_RECEIVE, 0, **read_log_page_args)
        if ioctl_ret != 0:
            raise phison.PhisonVSCFailedException(
                    f"Log page could not be read.\
                    Error code {hex(ioctl_ret)}")

        if use_security_receive:
            ioctl_ret, log_data = self._do_security_receive(
                phison.PhisonSecuritySendReceiveMajorCommand.\
                    PHISON_SECURITY_MAJOR_COMMAND_HANDLE_VSC,
                phison.PhisonSecuritySendReceiveMinorCommand.\
                    PHISON_SECURITY_MINOR_COMMAND_RECEIVE_VSC_DATA,
                size)
            if ioctl_ret != 0:
                raise phison.PhisonVSCFailedException(
                    f"Security Receive of log page failed!\
                    Error code {hex(ioctl_ret)}")

        return log_data

    def phison_fw_download(self, fw_file_path : str, chunk_size : int):
        """Download FW data to the controller via Phison VSC.

		:param fw_file_path: The path to FW binary.
		:type fw_file_path: str
		:param chunk_size: The chunk size to use for downloading.
		:type chunk_size: int
        :raises ValueError: Invalid chunk size or empty FW file.
        :raises phison.PhisonVSCFailedException: Error in VSC processing.

        .. note:: chunk_size must be >= 4 and <= nvme_common.NVME_MAX_TRANSFER_SIZE.
		"""
        if chunk_size < 4 or chunk_size > nvme_common.NVME_MAX_TRANSFER_SIZE:
            raise ValueError("Invalid chunk size provided!")

        with open(fw_file_path, 'rb') as f:
            fw_data = f.read()

        fw_data_len = len(fw_data)
        if fw_data_len == 0:
            raise ValueError("Empty file provided!")

        if chunk_size > fw_data_len:
            chunk_size = fw_data_len

        for curr_offset in range(0, fw_data_len, chunk_size):
            curr_chunk_size = min(chunk_size, fw_data_len - curr_offset)
            curr_chunk = fw_data[curr_offset : ][ : curr_chunk_size]

            self._phison_fw_download_chunk(curr_offset, curr_chunk)


    @phison_vsc
    def phison_fw_commit(self, slot : int, action : nvme_common.NVMECommitAction):
        """Commit a previously-downloaded firmware image via Phison VSC.

		:param slot: The firmware slot.
		:type slot: int
		:param action: The action to use when commiting the image.
		:type action: nvme_common.NVMECommitAction
		:raises ValueError: Invalid firmware slot.
		:raises phison.PhisonVSCFailedException: Failure commiting the image.
		"""
        if slot < 0 or slot > 7:
            raise ValueError("Valid firmware slot value is in the range 0 - 7")

        commit_args = {'cdw12' : (nvme_common.NVMEOpcode.NVME_FW_COMMIT.value << 8) |\
                       phison.PhisonVSCSubCmd.PHISON_VSC_EXECUTE_STANDARD.value,
		                'cdw13' : slot | (action.value << 3)}

        ret_code, _ = self._send_phison_vsc(phison.PhisonVSCCmd.PHISON_CONFIGURE, 0, **commit_args)
        if ret_code != 0:
            raise phison.PhisonVSCFailedException(f"Commit failed. Error code {hex(ret_code)}")


    @phison_vsc
    def phison_identify(self, cns : nvme_common.NVMEIdentifyCNS,
                        csi : nvme_common.NVMECSI) -> nvme_common.NVMEIdentifyBuffer:
        """Identify command via Phison VSC.

		:param cns: NVMe Controller or Namepace Structure.
		:type cns: nvme_common.NVMEIdentifyCNS
		:param csi: NVMe Command Set Identifier.
		:type csi: nvme_common.NVMECSI
		:return: The NVMe identify data.
		:rtype: nvme_common.NVMEIdentifyBuffer
		"""
        identify_buffer_size = ctypes.sizeof(nvme_common.NVMEIdentifyBuffer)

        identify_args = {'cdw10' : identify_buffer_size >> 2,
						'cdw12' :  (nvme_common.NVMEOpcode.NVME_IDENTIFY.value << 8) |\
                            phison.PhisonVSCSubCmd.PHISON_VSC_EXECUTE_STANDARD.value,
						'cdw13' : cns.value,
						'cdw14' : csi.value << 24,
						'data_len' : identify_buffer_size}

        ret_code, identify_buffer = self._send_phison_vsc(
            phison.PhisonVSCCmd.PHISON_RECEIVE, 0, **identify_args)

        identify_data = nvme_common.NVMEIdentifyBuffer.from_buffer_copy(identify_buffer)
        if ret_code != 0:
            raise phison.PhisonVSCFailedException(f"Identify failed. Error code {hex(ret_code)}")

        return identify_data


    def phison_security_move_phase2(self, security_fw_file_path : str):
        """Move to Security Access phase 2 (send security FW).

		:param security_fw_file_path: The path to the security FW binary to use.
		:type security_fw_file_path: str
		:raises phison.Phase2RecoverableException: Upon encountering a recoverable condition.
		:raises phison.Phase2UnexpectedException: Any other unexpected condition.
        
        .. note:: The controller must not have initiated a Security Access process.
		"""
        try:
            self.phison_fw_download(security_fw_file_path, 0x1000)
            self.phison_fw_commit(0, nvme_common.NVMECommitAction.NVME_FW_COMMIT_CA_REPLACE)
        except nvme_common.NVMEFwCommitException as exc:
            raise phison.Phase2RecoverableException(
                "Either security FW image is invalid or a reset attempt should be made") from exc
        except (nvme_common.NVMEFwDownloadException, Exception) as exc:
            raise phison.Phase2UnexpectedException(
                "Unexpected exception at 2nd phase, cannot continue") from exc

    @phison_vsc
    def phison_security_move_phase3(self):
        """Move to Security Access phase 3 (switch to challenge reception).

		:raises phison.Phase3GeneralException: VSC failure.
        
        .. note:: The controller must be in phase 2.
		"""
        self.unlock_vsc()

        security_args = {'cdw12' : phison.PhisonVSCSubCmd.PHISON_VSC_SECURITY_PHASE3.value}

        ret_code, _ = self._send_phison_vsc(
            phison.PhisonVSCCmd.PHISON_CONFIGURE, 0, **security_args)
        if ret_code != 0:
            raise phison.Phase3GeneralException(
                f"Moving to phase 3 failed. Error code {hex(ret_code)}")


    @phison_vsc
    def phison_security_move_phase4(self) -> bytes:
        """Move to Security Access phase 4 (receive challenge data).

        :raises phison.Phase4GeneralException: VSC failure.
        :return: The challenge data.
        :rtype: bytes

        .. note:: The controller must be in phase 3.
		"""
        security_args = {'cdw10' : phison.PHISON_SECURITY_CHALLENGE_SIZE >> 2,
						'cdw12' : phison.PhisonVSCSubCmd.PHISON_VSC_SECURITY_PHASE4.value,
						'data_len' : phison.PHISON_SECURITY_CHALLENGE_SIZE}

        ret_code, ret_buf = self._send_phison_vsc(
            phison.PhisonVSCCmd.PHISON_RECEIVE, 0, **security_args)
        if ret_code != 0:
            raise phison.Phase4GeneralException(
                f"Moving to phase 4 failed. Error code {hex(ret_code)}")

        assert len(ret_buf) == phison.PHISON_SECURITY_CHALLENGE_SIZE

        return ret_buf

    @phison_vsc
    def phison_security_move_phase5(self, response : bytes):
        """Move to Security Access phase 4 (send response data).

		:param response: The response to the challenge.
		:type response: bytes
        :raises ValueError: Invalid response size.
        :raises phison.InvalidSecurityResponseException: The response is not correct.
        :raises phison.Phase5GeneralException: Any other error.
        
        .. note:: The controller must be in phase 4.
		"""
        if len(response) != phison.PHISON_SECURITY_CHALLENGE_SIZE:
            raise ValueError(
                f"Response must be of size \
                    {hex(phison.PHISON_SECURITY_CHALLENGE_SIZE)} bytes exactly!")

        security_args = {'cdw10' : len(response) >> 2,
						'cdw11' : len(response),
						'cdw12' : phison.PhisonVSCSubCmd.PHISON_VSC_SECURITY_PHASE5.value,
						'data' : response, 
						'data_len' : len(response)}

        ret_code, _ = self._send_phison_vsc(phison.PhisonVSCCmd.PHISON_SEND, 0, **security_args)
        cmd_status_code = ret_code & 0xFF
        if ret_code != 0:
            exc_message = f"Moving to phase 5 failed. Error code {hex(ret_code)}"
            if cmd_status_code == 0:
                raise phison.InvalidSecurityResponseException(exc_message)
            raise phison.Phase5GeneralException(exc_message)


    @phison_vsc
    def phison_memory_write(self, address : int, data : bytes):
        """Write to arbitrary controller memory.

		:param address: The address to write to.
		:type address: int
		:param data: The data to write.
		:type data: bytes
        :raises ValueError: Invalid data size.
        :raises phison.PhisonVSCFailedException: Error in VSC processing.

        .. note:: The controller must have entered Security Access.
        .. note:: size of data must be >= 4 and <= phison.PHISON_RW_CHUNK_SIZE.
		"""
        data_len = len(data)
        if data_len > phison.PHISON_RW_CHUNK_SIZE or data_len < 4 :
            raise ValueError(
                "Size of write data cannot exceeded the max r/w size, not can it be less than 4!")

        write_args = {'cdw10' : len(data) >> 2,
						'cdw12' : phison.PhisonVSCSubCmd.PHISON_VSC_MEM_WRITE.value,
						'cdw13' : address,
						'cdw14' : len(data),
						'data' : data,
						'data_len' : len(data)}

        ret_code, _ = self._send_phison_vsc(phison.PhisonVSCCmd.PHISON_SEND, 0, **write_args)
        if ret_code != 0:
            raise phison.PhisonVSCFailedException(
                f"Memory write failed. Error code {hex(ret_code)}")


    @phison_vsc
    def phison_memory_read(self, address : int, size : int, core : int = 0) -> bytes:
        """Read from arbitrary controller memory.

		:param address: The address to read from.
		:type address: int
		:param size: The number of bytes to read.
        :type size: int
        :raises ValueError: The number of bytes to read is invalid.
        :raises phison.PhisonVSCFailedException: Error in VSC processing.
        :return: The data read.
        :rtype: bytes

        .. note:: The controller must have entered Security Access.
        .. note:: read size must be >= 4 and <= phison.PHISON_RW_CHUNK_SIZE.
		"""
        if size > phison.PHISON_RW_CHUNK_SIZE or size < 4:
            raise ValueError(
                "Read size cannot exceed the max r/w size, nor can it be less than 4!")

        read_args = {'cdw10' : size >> 2,
                        'cdw11' : core,
						'cdw12' : phison.PhisonVSCSubCmd.PHISON_VSC_MEM_READ.value,
						'cdw13' : address,
						'cdw14' : size,
						'data_len' : size}

        ret_code, ret_buf = self._send_phison_vsc(
            phison.PhisonVSCCmd.PHISON_RECEIVE, 0, **read_args)
        if ret_code != 0:
            raise phison.PhisonVSCFailedException(f"Memory read failed. Error code {hex(ret_code)}")

        return ret_buf
