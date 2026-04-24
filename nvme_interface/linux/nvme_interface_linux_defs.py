import ctypes
from enum import Enum

class NVMEIoctl(Enum):
    """NVMe-related IO Control codes
	"""
    NVME_IOCTL_ADMIN_CMD = 0xC0484E41
    NVME_IOCTL_RESET = 0x4E44

class NVMEPassThrough(ctypes.Structure):
    """NVMe passthrough packet structure.
	"""
    _fields_ = [('opcode', ctypes.c_ubyte),
				('flags', ctypes.c_ubyte),
				('rsvd1', ctypes.c_uint16),
				('nsid', ctypes.c_uint32),
				('cdw2', ctypes.c_uint32),
				('cdw3', ctypes.c_uint32),
				('metadata', ctypes.c_uint64),
				('addr', ctypes.POINTER(ctypes.c_ubyte)),
				('metadata_len', ctypes.c_uint32),
				('data_len', ctypes.c_uint32),
				('cdw10', ctypes.c_uint32),
				('cdw11', ctypes.c_uint32),
				('cdw12', ctypes.c_uint32),
				('cdw13', ctypes.c_uint32),
				('cdw14', ctypes.c_uint32),
				('cdw15', ctypes.c_uint32),
				('timeout_ms', ctypes.c_uint32),
				('result', ctypes.c_uint32)]
    _pack_ = 1
