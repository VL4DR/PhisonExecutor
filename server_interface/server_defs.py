import ctypes
from enum import Enum

# Server magic used for requests/responses
DEFAULT_MAGIC = 0xDEADBEEF

# The maximum size of the data portion of requests/responses
DEFAULT_MAX_SERVER_DATA_SIZE = 0x100

# The maximum size of shellcode binary
DEFAULT_SHELLCODE_BUFFER_SIZE = 0x1000

class ServerOpcode(Enum):
    """The command codes that the Server supports.
    """
    SERVER_OPCODE_NOP = 0
    SERVER_OPCODE_RESET_STATE = 1
    SERVER_OPCODE_READ = 2
    SERVER_OPCODE_WRITE = 3
    SERVER_OPCODE_CALL = 4
    SERVER_OPCODE_TRANSFER_INITIATE = 5
    SERVER_OPCODE_TRANSFER_DATA = 6
    SERVER_OPCODE_EXECUTE = 7
    SERVER_OPCODE_CUSTOM = 8


class ServerStatus(Enum):
    """The status codes the Server may return.
    """
    SERVER_SUCCESS = 0
    SERVER_NULL_PARAMETER = 1
    SERVER_INVALID_PARAMETER = 2
    SERVER_UNIMPLEMENTED = 3
    SERVER_INVALID_MAGIC = 4
    SERVER_INTERNAL_ERROR = 5
    SERVER_INVALID_STATE = 6


class ServerRequestHeader(ctypes.Structure):
    """Every Server request starts with this header.
    """
    _pack_ = 1
    _fields_ = [('magic', ctypes.c_uint32),
                ('opcode', ctypes.c_uint32),
                ('length', ctypes.c_uint32),
                ('subcommand', ctypes.c_uint32),
                ('integrity', ctypes.c_uint32)]


class ServerResponseHeader(ctypes.Structure):
    """Every Server response starts with this header.
    """
    _pack_ = 1
    _fields_ = [('magic', ctypes.c_uint32),
                ('opcode', ctypes.c_uint32),
                ('length', ctypes.c_uint32),
                ('status', ctypes.c_uint32),
                ('integrity', ctypes.c_uint32)]


class ServerReadRequest(ctypes.Structure):
    """Server Read Memory request structure.
    """
    _pack_ = 1
    _fields_ = [('address', ctypes.c_uint64),
                ('size', ctypes.c_uint32)]


class ServerWriteRequest(ctypes.Structure):
    """Server Write Memory request structure.
    """
    _pack_ = 1
    _fields_ = [('address', ctypes.c_uint64)]


class ServerCallRequest(ctypes.Structure):
    """Server Call request structure.
    """
    _pack_ = 1
    _fields_ = [('address', ctypes.c_uint64),
                ('arg1', ctypes.c_uint64),
                ('arg2', ctypes.c_uint64),
                ('arg3', ctypes.c_uint64),
                ('arg4', ctypes.c_uint64)]


class ServerTransferInitiateRequest(ctypes.Structure):
    """Server Transfer Initiate request structure.
    """
    _pack_ = 1
    _fields_ = [('shellcode_size', ctypes.c_uint32)]


class ServerTransferDataRequest(ctypes.Structure):
    """Server Transfer Data request structure.
    """
    _pack_ = 1
    _fields_ = [('offset', ctypes.c_uint32)]


class InvalidMagicException(Exception):
    """The response magic is not correct.
    """

# The maximum size possible for a single server response frame.
MAX_SERVER_RESPONSE_SIZE = ctypes.sizeof(ServerResponseHeader) + DEFAULT_MAX_SERVER_DATA_SIZE

# The maximum size of the data chunk that may be transferred at a time.
MAX_TRANSFER_CHUNK_SIZE = DEFAULT_MAX_SERVER_DATA_SIZE - ctypes.sizeof(ServerTransferDataRequest)

# The maximum chunk size that may be received in a single Read command.
MAX_READ_CHUNK_SIZE = DEFAULT_MAX_SERVER_DATA_SIZE

# The maximum chunk size that may be sent in a single Write command.
MAX_WRITE_CHUNK_SIZE = DEFAULT_MAX_SERVER_DATA_SIZE - ctypes.sizeof(ServerWriteRequest)
