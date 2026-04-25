from server_interface import server_defs

class ServerInterface:

    @staticmethod
    def _build_server_request(opcode : int, request_data : bytes) -> bytes:
        """Build the entire server request including metadata.
        """
        magic = server_defs.DEFAULT_MAGIC
        request_header = server_defs.ServerRequestHeader.build(dict(magic=magic, opcode=opcode, length=len(request_data), subcommand=0, integrity=0))
        return b''.join([request_header, request_data])
    

    @staticmethod
    def parse_server_response(response : bytes) -> tuple[server_defs.ServerStatus, bytes]:
        """Return Server response code and data.
        
        :param response: The raw response data bytes.
        :type response: bytes
        :return: Server status code and data.
        :rtype: tuple[server_defs.ServerStatus, bytes]
        """
        response_header = server_defs.ServerResponseHeader.parse(response)
        response_header_length = server_defs.ServerResponseHeader.sizeof()
        data_length = response_header.length

        return server_defs.ServerStatus(response_header.status), response[response_header_length : ][ : data_length]


    @staticmethod
    def build_read_memory_request(address : int, size : int) -> bytes:
        """Build Read Memory request.

        :param address: Address to read from.
        :type address: int
        :param size: Number of bytes to read.
        :type size: int
        :return: Raw request bytes.
        :rtype: bytes
        """
        read_request_data = server_defs.ServerReadRequest.build(dict(address=address, size=size))
        read_request = ServerInterface._build_server_request(server_defs.ServerOpcode.SERVER_OPCODE_READ.value, read_request_data)
        
        return read_request


    @staticmethod
    def build_write_memory_request(address : int, data : bytes) -> bytes:
        """Build Write Memory request.

        :param address: Address to read to.
        :type address: int
        :param size: Number of bytes to write.
        :type size: int
        :return: Raw request bytes.
        :rtype: bytes
        """
        write_request_data = b''.join([server_defs.ServerWriteRequest.build(dict(address=address)), data])
        write_request = ServerInterface._build_server_request(server_defs.ServerOpcode.SERVER_OPCODE_WRITE.value, write_request_data)
        
        return write_request


    @staticmethod
    def build_call_function_request(address : int, arg1 : int, arg2 : int, arg3 : int, arg4 : int) -> bytes:
        """Build Call request.

        :param address: Address to call.
        :type address: int
        :param arg1: First argument.
        :type size: int
        :param arg2: Second argument.
        :type size: int
        :param arg3: Third argument.
        :type size: int
        :param arg4: Fourth argument.
        :type size: int
        :return: Raw request bytes.
        :rtype: bytes
        """
        call_request_data = server_defs.ServerCallRequest.build(dict(address=address, arg1=arg1, arg2=arg2, arg3=arg3, arg4=arg4))
        call_request = ServerInterface._build_server_request(server_defs.ServerOpcode.SERVER_OPCODE_CALL.value, call_request_data)
        
        return call_request


    @staticmethod
    def build_initiate_data_transfer_request(shellcode_size : int) -> bytes:
        """Build Initiate Data Transfer request.

        :param shellcode_size: Size of shellcode to transfer.
        :type shellcode_size: int
        :return: Raw request bytes.
        :rtype: bytes
        """
        initiate_data_transfer_data = server_defs.ServerTransferInitiateRequest.build(dict(shellcode_size=shellcode_size))
        initiate_data_transfer_request = ServerInterface._build_server_request(server_defs.ServerOpcode.SERVER_OPCODE_TRANSFER_INITIATE.value, initiate_data_transfer_data)

        return initiate_data_transfer_request
    

    @staticmethod
    def build_transfer_data_request(offset : int, data : bytes) -> bytes:
        """Build Transfer Data request.

        :param offset: Offset to write chunk to.
        :type offset: int
        :param data: The chunk data.
        :type data: bytes
        :return: Raw request bytes.
        :rtype: bytes
        """
        transfer_data_request_data = b''.join([server_defs.ServerTransferDataRequest.build(dict(offset=offset)), data])
        transfer_data_request = ServerInterface._build_server_request(server_defs.ServerOpcode.SERVER_OPCODE_TRANSFER_DATA.value, transfer_data_request_data)
        
        return transfer_data_request
    

    @staticmethod
    def build_call_shellcode_request() -> bytes:
        """Build Call Shellcode request.

        :return: Raw request bytes.
        :rtype: bytes
        """
        execute_request = ServerInterface._build_server_request(server_defs.ServerOpcode.SERVER_OPCODE_EXECUTE.value, b'')

        return execute_request


    @staticmethod
    def reset_state() -> bytes:
        """Build Reset State request.

        :return: Raw request bytes.
        :rtype: bytes
        """
        reset_state_request = ServerInterface._build_server_request(server_defs.ServerOpcode.SERVER_OPCODE_RESET_STATE.value, b'')
    
        return reset_state_request
