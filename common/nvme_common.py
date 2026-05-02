import ctypes
from enum import Enum

class NVMEOpcode(Enum):
    """Currently supported NVMe commands.
    """
    NVME_GET_LOG_PAGE = 0x02
    NVME_IDENTIFY = 0x06
    NVME_FW_COMMIT = 0x10
    NVME_FW_DOWNLOAD = 0x11
    NVME_SECURITY_SEND = 0x81
    NVME_SECURITY_RECEIVE = 0x82

class NVMECommitAction(Enum):
    """NVMe Commit actions.
    """
    NVME_FW_COMMIT_CA_REPLACE = 0
    NVME_FW_COMMIT_CA_REPLACE_AND_ACTIVATE = 1
    NVME_FW_COMMIT_CA_SET_ACTIVE = 2
    NVME_FW_COMMIT_CA_REPLACE_AND_ACTIVATE_IMMEDIATE = 3
    NVME_FW_COMMIT_CA_REPLACE_BOOT_PARTITION = 6
    NVME_FW_COMMIT_CA_ACTIVATE_BOOT_PARTITION = 7

class NVMEIdentifyCNS(Enum):
    """NVMe Controller or Namepace Structures.
    """
    NVME_CNS_CONTROLLER = 1

class NVMECSI(Enum):
    """NVMe Command Set Identifier.
    """
    NVME_CSI_NVM = 0

NVME_IDENTIFY_REST_FIELDS_SIZE = 0xFAC
class NVMEIdentifyBuffer(ctypes.Structure):
    """NVMe Identify buffer structure.
    """
    _pack_ = 1
    _fields_ = [
		("vid", ctypes.c_uint16),
		("ssvid", ctypes.c_uint16),
		("sn", ctypes.c_char * 20),
		("mn", ctypes.c_char * 40),
		("fr", ctypes.c_char * 20),
		("rest", ctypes.c_ubyte * NVME_IDENTIFY_REST_FIELDS_SIZE)
	]


# These defines are not NVMe specific,
# but rather some common parameters that will be used for making NVMe requests.
NVME_MAX_TRANSFER_SIZE = 0x20000
NVME_STANDARD_TIMEOUT_SECONDS = 10

class NVMEFwCommitException(Exception):
    """NVMe Commit failure.
    """

class NVMEFwDownloadException(Exception):
    """NVMe download failure.
    """
