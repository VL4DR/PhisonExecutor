import ctypes
import ctypes.wintypes as wintypes
from ctypes import windll
from enum import Enum

STORAGE_PROTOCOL_STRUCTURE_VERSION = 0x01
IOCTL_STORAGE_PROTOCOL_COMMAND = 0x002DD3C0
IOCTL_SCSI_PASSTHROUGH_DIRECT = 0x0004D014
IOCTL_STORAGE_GET_DEVICE_NUMBER = 0x002D1080
SCSI_CDB_LENGTH = 0x10
SCSI_SENSE_INFO_LENGTH = 0x18
PROTOCOL_TYPE_NVME = 0x00000003
STORAGE_PROTOCOL_COMMAND_FLAG_ADAPTER_REQUEST = 0x80000000
STORAGE_PROTOCOL_SPECIFIC_NVME_ADMIN_COMMAND = 0x01
STORAGE_PROTOCOL_STATUS_SUCCESS = 1

CDB_CODE_SEND_SQ = 0xC000FEB5
CDB_CODE_TRIGGER_WRITE = 0xC100FEB5
CDB_CODE_READ = 0xC200FEA2
CDB_SUB_CODE_SEND_SQ = 0x40000000
CDB_SUB_CODE_TRIGGER = 0x20000
SCSI_TRIGGER_BUFFER_LENGTH = 0x200

class IoctlMethod(Enum):
    """Windows driver IO Control methods.
	"""
    IOCTL_METHOD_SCSI_PASSTHROUGH_DIRECT = 0x00
    IOCTL_METHOD_NVME_STORAGE_PROTOCOL = 0x01


class DataDirection(Enum):
    """Data transfer direction.
	"""
    DIRECTION_OUT = 0
    DIRECTION_IN = 1


class CDBOperation(Enum):
    """CDB operation types.
	"""
    SCSI_SEND_SQ = 0
    SCSI_TRIGGER = 1
    SCSI_WRITE_DATA = 2
    SCSI_READ_DATA = 3


class NVMECmd(ctypes.Structure):
    """NVMe command structure.
	"""
    _pack_ = 1
    _fields_ = [('opcode', ctypes.c_ubyte),
				('zero0', ctypes.c_ubyte * 3),
				('nsid', ctypes.c_uint32),
				('zero1', ctypes.c_ubyte * 32),
				('cdw10', ctypes.c_uint32),
				('cdw11', ctypes.c_uint32),
				('cdw12', ctypes.c_uint32),
				('cdw13', ctypes.c_uint32),
				('cdw14', ctypes.c_uint32),
				('cdw15', ctypes.c_uint32)]


class StorageProtocolCommand(ctypes.Structure):
    """Storage Protocol command structure.
	"""
    # @todo check packing.
    #_pack_ = 1
    _fields_ = [('version', wintypes.DWORD),
				('length', wintypes.DWORD),
				('protocol_type', wintypes.DWORD),
				('flags', wintypes.DWORD),
				('return_status', wintypes.DWORD),
				('error_code', wintypes.DWORD),
				('command_length', wintypes.DWORD),
				('error_info_length', wintypes.DWORD),
				('data_to_device_transfer_length', wintypes.DWORD),
				('data_from_device_transfer_length', wintypes.DWORD),
				('timeout', wintypes.DWORD),
				('error_info_offset', wintypes.DWORD),
				('data_to_device_buffer_offset', wintypes.DWORD),
				('data_from_device_buffer_offset', wintypes.DWORD),
				('command_specific', wintypes.DWORD),
				('reserved0', wintypes.DWORD),
				('fixed_protocol_return_data', wintypes.DWORD),
				('fixed_protocol_return_data2', wintypes.DWORD),
				('reserved1', 2 * wintypes.DWORD),
				('command', ctypes.c_ubyte)]


class SCSIPassThroughDirect(ctypes.Structure):
    """Passthrough SCSI direct mode frame structure.
    """
    # @todo check packing.
    #_pack_ = 1
    _fields_ = [
		('length', ctypes.c_uint16),
		('scsi_status', ctypes.c_uint8),
		('path_id', ctypes.c_uint8),
		('target_id', ctypes.c_uint8),
		('lun', ctypes.c_uint8),
		('cdb_length', ctypes.c_uint8),
		('sense_info_length', ctypes.c_uint8),
		('data_in', ctypes.c_uint8),
		('data_transfer_length', ctypes.c_ulong),
		('timeout', ctypes.c_ulong),
		('data_buffer', wintypes.LPVOID),
		('sense_info_offset', ctypes.c_ulong),
		('cdb', (ctypes.c_ubyte * SCSI_CDB_LENGTH))
	]


class SCSICDBData(ctypes.Structure):
    """SCSI CDB data structure.
	"""
    _pack_ = 1
    _fields_ = [
		('main_code', ctypes.c_uint32),
		('unk0', ctypes.c_uint8),
		('unk1', ctypes.c_uint8),
		('sub_code', ctypes.c_uint32),
		('unk2', ctypes.c_uint32),
		('unk3', ctypes.c_uint16),
	]


# Windows file-related definitions.
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000

OPEN_EXISTING = 3

FILE_ATTRIBUTE_NORMAL = 0x00000080

INVALID_HANDLE_VALUE = -1

# CreateFileA WinAPI definition.
CreateFileA = windll.kernel32.CreateFileA
CreateFileA.argtypes = [
		wintypes.LPCSTR,
		wintypes.DWORD,
		wintypes.DWORD,
		wintypes.LPVOID,
		wintypes.DWORD,
		wintypes.DWORD,
		wintypes.HANDLE]
CreateFileA.restype = wintypes.HANDLE

# CloseFileA WinAPI definition.
CloseHandle = windll.kernel32.CloseHandle
CloseHandle.argtypes = [
		wintypes.HANDLE
]
CloseHandle.restype = None

# DeviceIoControl WinAPI definition.
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
