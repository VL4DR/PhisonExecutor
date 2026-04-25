from enum import Enum
import construct as cs

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


# Every Server request starts with this header.
ServerRequestHeader = cs.Struct(
    "magic" / cs.Int32ul,
    "opcode" / cs.Int32ul,
    "length" / cs.Int32ul,
    "subcommand" / cs.Int32ul,
    "integrity" / cs.Int32ul,
)


# Every Server response starts with this header.
ServerResponseHeader = cs.Struct(
    "magic" / cs.Int32ul,
    "opcode" / cs.Int32ul,
    "length" / cs.Int32ul,
    "status" / cs.Int32ul,
    "integrity" / cs.Int32ul,
)


# Server Read Memory request structure.
ServerReadRequest = cs.Struct(
    "address" / cs.Int64ul,
    "size" / cs.Int32ul
)


# Server Write Memory request structure.
ServerWriteRequest = cs.Struct(
    "address" / cs.Int64ul
)


# Server Call request structure.
ServerCallRequest = cs.Struct(
    "address" / cs.Int64ul,
    "arg1" / cs.Int64ul,
    "arg2" / cs.Int64ul,
    "arg3" / cs.Int64ul,
    "arg4" / cs.Int64ul
)


# Server Transfer Initiate request structure.
ServerTransferInitiateRequest = cs.Struct(
    "shellcode_size" / cs.Int32ul
)


# Server Transfer Data request structure.
ServerTransferDataRequest = cs.Struct(
    "offset" / cs.Int32ul
)


# The maximum size possible for a single server response frame.
MAX_SERVER_RESPONSE_SIZE = ServerResponseHeader.sizeof() + DEFAULT_MAX_SERVER_DATA_SIZE
