import ctypes
from enum import Enum

class PhisonCRCData(ctypes.Structure):
	_fields_ = [('opcode', ctypes.c_ubyte),
				('zero', ctypes.c_ubyte * 39),
				('cdw10', ctypes.c_uint32),
				('cdw11', ctypes.c_uint32),
				('cdw12', ctypes.c_uint32),
				('cdw13', ctypes.c_uint32),
				('cdw14', ctypes.c_uint32),
				('cdw15', ctypes.c_uint32)]
				
VSC_UNLOCK_MAGIC = 0xFAEFFE6F

class PhisonVSCCmd(Enum):
	PHISON_CONFIGURE = 0xD0
	PHISON_SEND = 0xD1
	PHISON_RECEIVE = 0xD2

class PhisonVSCSubCmd(Enum):
	PHISON_VSC_MEM_WRITE = 0x20
	PHISON_VSC_MEM_READ = 0xA0
	PHISON_VSC_SECURITY_PHASE3 = 0xC4
	PHISON_VSC_SECURITY_PHASE4 = 0xC5
	PHISON_VSC_SECURITY_PHASE5 = 0xC6
	PHISON_VSC_EXECUTE_STANDARD = 0xFF


PHISON_SECURITY_AES_IV = b"\x82\xC7\x15\x82\x38\xAF\xE2\x08\xE1\x26\x57\xEF\x09\x1A\x73\x99"
PHISON_SECURITY_AES_KEY_SIZE = 0x20
PHISON_SECURITY_CHALLENGE_SIZE = 0x200
PHISON_SECURITY_CHALLENGE_ENCRYPTED_PART_SIZE = 0x100

PHISON_NVME_BUFFER_SIZE = 0x20000

class Phase2RecoverableException(Exception):
	pass

class Phase2UnexpectedException(Exception):
	pass

class Phase3GeneralException(Exception):
	pass

class Phase4GeneralException(Exception):
	pass

class Phase5GeneralException(Exception):
	pass

class InvalidSecurityResponseException(Exception):
	pass

class PhisonVSCFailedException(Exception):
	pass
	