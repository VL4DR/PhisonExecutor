import ctypes
import ctypes.wintypes as wintypes
from ctypes import windll
from enum import Enum

class IoctlMethod(Enum):
	IOCTL_METHOD_SCSI_PASSTHROUGH_DIRECT = 0x00
	IOCTL_METHOD_NVME_STORAGE_PROTOCOL = 0x01

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

class DataDirection(Enum):
	DIRECTION_OUT = 0
	DIRECTION_IN = 1

class CDBOperation(Enum):
	SCSI_SEND_SQ = 0
	SCSI_TRIGGER = 1
	SCSI_WRITE_DATA = 2
	SCSI_READ_DATA = 3

class NVMECmd(ctypes.Structure):
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

class Guid(ctypes.Structure):
	_fields_ = [('data1', ctypes.c_uint32),
				('data2', ctypes.c_uint16),
				('data3', ctypes.c_uint16),
				('data4', 8 * ctypes.c_ubyte)]

class SPDevInfoData(ctypes.Structure):
	_fields_ = [('cb_size', wintypes.DWORD),
				('class_guid', Guid),
				('dev_inst', wintypes.DWORD),
				('reserved', ctypes.POINTER(ctypes.c_ulong))]

class SPDeviceInterfaceData(ctypes.Structure):
	_fields_ = [('cb_size', wintypes.DWORD),
				('interface_class_guid', Guid),
				('flags', wintypes.DWORD),
				('reserved', ctypes.POINTER(ctypes.c_ulong))]

class SPDeviceInterfaceDetailDataA(ctypes.Structure):
	_fields_ = [('cb_size', wintypes.DWORD),
				('device_path', (ctypes.c_char * 1))]
	
class SCSIPassThroughDirect(ctypes.Structure):
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
	_pack_ = 1
	_fields_ = [
		('main_code', ctypes.c_uint32),
		('unk0', ctypes.c_uint8),
		('unk1', ctypes.c_uint8),
		('sub_code', ctypes.c_uint32),
		('unk2', ctypes.c_uint32),
		('unk3', ctypes.c_uint16),
	]

class StorageDeviceNumber(ctypes.Structure):
	_fields_ = [('device_type', ctypes.c_uint16),
				('device_number', wintypes.DWORD),
				('partition_number', wintypes.DWORD)]

class Guid(ctypes.Structure):
	_fields_ = [('data1', ctypes.c_uint32),
				('data2', ctypes.c_uint16),
				('data3', ctypes.c_uint16),
				('data4', 8 * ctypes.c_ubyte)]

class SPDevInfoData(ctypes.Structure):
	_fields_ = [('cb_size', wintypes.DWORD),
				('class_guid', Guid),
				('dev_inst', wintypes.DWORD),
				('reserved', ctypes.POINTER(ctypes.c_ulong))]

class SPDeviceInterfaceData(ctypes.Structure):
	_fields_ = [('cb_size', wintypes.DWORD),
				('interface_class_guid', Guid),
				('flags', wintypes.DWORD),
				('reserved', ctypes.POINTER(ctypes.c_ulong))]

MAX_DEVICE_PATH_SIZE = 0x400
SP_DEVICE_INTERFACE_DETAIL_DATA_SIZEOF = 8
class SPDeviceInterfaceDetailData(ctypes.Structure):
	_fields_ = [('cb_size', wintypes.DWORD),
				('device_path', (ctypes.c_char * MAX_DEVICE_PATH_SIZE))]

class DiGetClassFlags(Enum):
	DIGCG_DEFAULT = 0x00000001
	DIGCF_PRESENT = 0x00000002
	DIGCF_DEVICEINTERFACE = 0x00000010

FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000

OPEN_EXISTING = 3

FILE_ATTRIBUTE_NORMAL = 0x00000080

INVALID_HANDLE_VALUE = -1

ERROR_INSUFFICIENT_BUFFER = 0x0000007A
ERROR_NO_MORE_ITEMS = 0x00000103

GUID_DEVINTERFACE_DISK = Guid(0x53F56307, 0xB6BF, 0x11D0, (ctypes.c_ubyte * 8).from_buffer_copy(b"\x94\xF2\x00\xA0\xC9\x1E\xFB\x8B"))

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

CloseHandle = windll.kernel32.CloseHandle
CloseHandle.argtypes = [
		wintypes.HANDLE
]
CloseHandle.restype = None

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
