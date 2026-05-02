import os
import ctypes
import fcntl
from common import nvme_common
import nvme_interface.linux.nvme_interface_linux_defs as nvme_linux

class NVMEInterface:
    """Linux NVMe command interface.
	"""
    def __init__(self, device_path : str):
        self._device = os.open(device_path, os.O_RDWR)

    def nvme_send_command(self, opcode : int, nsid : int, **kwargs : dict) -> tuple[int, bytes]:
        """Send an NVMe command to the controller.

		:param opcode: NVMe command code.
		:type opcode: int
		:param nsid: Namespace ID.
		:type nsid: int
		:raises ValueError: Invalid data or data length combination.
		:return: The ioctl return code and the NVMe buffer contents.
		:rtype: tuple[int, bytes]
		"""
        cmd = nvme_linux.NVMEPassThrough()
        cmd.opcode = opcode
        cmd.nsid = nsid
        ioctl_ret = 0

        if 'data' in kwargs and 'data_len' not in kwargs:
            raise ValueError("If 'data' is provided, then 'data_len' must also be provided")

        nvme_buffer = (ctypes.c_ubyte * 0)()
        if 'cdw10' in kwargs:
            cmd.cdw10 = kwargs['cdw10']
        if 'cdw11' in kwargs:
            cmd.cdw11 = kwargs['cdw11']
        if 'cdw12' in kwargs:
            cmd.cdw12 = kwargs['cdw12']
        if 'cdw13' in kwargs:
            cmd.cdw13 = kwargs['cdw13']
        if 'cdw14' in kwargs:
            cmd.cdw14 = kwargs['cdw14']
        if 'cdw15' in kwargs:
            cmd.cdw15 = kwargs['cdw15']
        if 'data_len' in kwargs:
            data_len = kwargs['data_len']
            if data_len < 0 or data_len > nvme_common.NVME_MAX_TRANSFER_SIZE:
                raise ValueError("Invalid length provided!")

            cmd.data_len = data_len
            if data_len != 0:
                if 'data' in kwargs:
                    if len(kwargs['data']) < data_len:
                        raise ValueError("Invalid combination of 'data' and 'data_len'!")
                    nvme_buffer_type = ctypes.c_ubyte * data_len
                    nvme_buffer = nvme_buffer_type.from_buffer_copy(kwargs['data'])
                else:
                    nvme_buffer = (ctypes.c_ubyte * data_len)()

                cmd.addr = nvme_buffer

        ioctl_ret = fcntl.ioctl(
            self._device, nvme_linux.NVMEIoctl.NVME_IOCTL_ADMIN_CMD.value, bytearray(cmd), 1)

        return ioctl_ret, bytes(nvme_buffer)
