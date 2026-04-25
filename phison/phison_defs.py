import ctypes
from enum import Enum

class PhisonCRCData(ctypes.Structure):
    """The Phison command data that CRC is done on.
	"""
    _fields_ = [('opcode', ctypes.c_ubyte),
				('zero', ctypes.c_ubyte * 39),
				('cdw10', ctypes.c_uint32),
				('cdw11', ctypes.c_uint32),
				('cdw12', ctypes.c_uint32),
				('cdw13', ctypes.c_uint32),
				('cdw14', ctypes.c_uint32),
				('cdw15', ctypes.c_uint32)]


class PhisonVSCCmd(Enum):
    """Phison VSC NVMe command codes.
	"""
    PHISON_CONFIGURE = 0xD0
    PHISON_SEND = 0xD1
    PHISON_RECEIVE = 0xD2


class PhisonVSCSubCmd(Enum):
    """Phison VSC subcommands used.
	"""
    PHISON_VSC_MEM_WRITE = 0x20
    PHISON_VSC_MEM_READ = 0xA0
    PHISON_VSC_SECURITY_PHASE3 = 0xC4
    PHISON_VSC_SECURITY_PHASE4 = 0xC5
    PHISON_VSC_SECURITY_PHASE5 = 0xC6
    PHISON_VSC_EXECUTE_STANDARD = 0xFF


class PhisonVSCLogPageId(Enum):
    """Phison VSC Log Page ID
    """
    PHISON_VSC_PAGE_ID_C6 = 0xC6


# The magic value used for unlocking Phison VSC.
VSC_UNLOCK_MAGIC = 0xFAEFFE6F


# Security Access related definitions.
PHISON_SECURITY_AES_IV = b"\x82\xC7\x15\x82\x38\xAF\xE2\x08\xE1\x26\x57\xEF\x09\x1A\x73\x99"
PHISON_SECURITY_AES_KEY_SIZE = 0x20
PHISON_SECURITY_CHALLENGE_SIZE = 0x200
PHISON_SECURITY_CHALLENGE_ENCRYPTED_PART_SIZE = 0x100


# Phison FW version string size in bytes.
PHISON_FW_NAME_SIZE = 8

# NVMe buffer size.
PHISON_NVME_BUFFER_SIZE = 0x20000

# Maximum size that can be read/write at a time.
PHISON_RW_CHUNK_SIZE = 0x100


class Phase2RecoverableException(Exception):
    """Security Access phase 2 expected and recoverable exception.
	"""


class Phase2UnexpectedException(Exception):
    """Security Access phase 2 unexpected exception.
	"""


class Phase3GeneralException(Exception):
    """Security Access phase 3 generic exception.
	"""


class Phase4GeneralException(Exception):
    """Security Access phase 4 generic exception.
	"""


class Phase5GeneralException(Exception):
    """Security Access phase 5 generic exception.
	"""


class InvalidSecurityResponseException(Exception):
    """Response to challenge was incorrect.
	"""


class PhisonVSCFailedException(Exception):
    """Generic exception indicating Phison VSC failure.
	"""
