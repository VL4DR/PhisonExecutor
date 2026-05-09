import time
import logging
import ctypes
from functools import reduce
from Crypto.Cipher import AES
from Crypto.Util.number import bytes_to_long, long_to_bytes
from phison_executor import phison_executor_defs
import phison_executor.exceptions as executor_exceptions
from phison import phison_defs
from phison.phison_layer import PhisonLayer
from server_interface.server_interface import ServerInterface
from server_interface import server_defs

logger = logging.getLogger(__name__)

class PhisonExecutor:
    """The Executor object through which RWX functionality is given.
    """
    def __init__(self, device_path : str):
        self._phison = PhisonLayer(device_path)

        system_info = self._get_system_info()

        security_access_enabled = PhisonExecutor._is_security_access_enabled(system_info)

        logger.info("Starting PhisonExecutor...")

        fw_version = PhisonExecutor._get_fw_version(system_info)
        logger.info(f"Controller FW version {fw_version}")
        if fw_version not in phison_executor_defs.PHISON_EXECUTOR_DEFS:
            raise executor_exceptions.FirmwareUnsupportedException(
                f"FW version {fw_version} is currently unsupported!")

        self._fw_defs = phison_executor_defs.PHISON_EXECUTOR_DEFS[fw_version]

        with open(self._fw_defs['modulus_path'], 'rb') as f:
            self._modulus_bytes = f.read()

        with open(self._fw_defs['exp_path'], 'rb') as f:
            self._exp_bytes = f.read()

        with open(self._fw_defs['server_binary_path'], 'rb') as f:
            server_binary = f.read()

        with open(self._fw_defs['server_trampoline_binary_path'], 'rb') as f:
            trampoline_binary = f.read()

        if not security_access_enabled:
            logger.info("Security Access is not enabled. Initiating...")
            self._enable_security_access()

        if not self._is_server_up(server_binary):
            logger.info("Server is not up. Installing...")
            self._install_server(server_binary, trampoline_binary)


    @staticmethod
    def _get_plain_challenge_part(challenge_data : bytes) -> bytes:
        """Get the plain part of the challenge.

        :param challenge_data: The challenge data.
        :type challenge_data: bytes
        :return: The plain part of the challenge.
        :rtype: bytes
        """
        assert len(challenge_data) == phison_defs.PHISON_SECURITY_CHALLENGE_SIZE
        return challenge_data[phison_defs.PHISON_SECURITY_CHALLENGE_ENCRYPTED_PART_SIZE : ]


    @staticmethod
    def _get_encrypted_challenge_part(challenge_data : bytes) -> bytes:
        """Get the encrypted part of the challenge.

        :param challenge_data: The challenge data.
        :type challenge_data: bytes
        :return: The encrypted part of the challenge.
        :rtype: bytes
        """
        assert len(challenge_data) == phison_defs.PHISON_SECURITY_CHALLENGE_SIZE
        return challenge_data[ : phison_defs.PHISON_SECURITY_CHALLENGE_ENCRYPTED_PART_SIZE]


    @staticmethod
    def _xor_buffers(buffer_a : bytes, buffer_b : bytes) -> bytes:
        """Perform a byte-by-byte xor operation on two byte sequences.

        :param buffer_a: First byte sequence.
        :type buffer_a: bytes
        :param buffer_b: Second byte sequence
        :type buffer_b: bytes
        :return: The result of xoring the byte sequences.
        :rtype: bytes

        .. note:: Both buffers must be of equal size.
        """
        assert len(buffer_a) == len(buffer_b)
        return bytes([buffer_a[i] ^ buffer_b[i] for i in range(len(buffer_a))])


    @staticmethod
    def _split_to_key_size_chunks(some_bytes : bytes) -> list:
        """Split a byte sequence to chunks of the AES encryption key size.

        :param some_bytes: Input byte sequence.
        :type some_bytes: bytes
        :return: The list containing the key-sized chunks from input.
        :rtype: list
        """
        assert len(some_bytes) % phison_defs.PHISON_SECURITY_AES_KEY_SIZE == 0
        lst = []
        for i in range(0, len(some_bytes), phison_defs.PHISON_SECURITY_AES_KEY_SIZE):
            lst.append(some_bytes[i : i + phison_defs.PHISON_SECURITY_AES_KEY_SIZE])

        return lst


    @staticmethod
    def _get_fw_version(system_info : phison_defs.PhisonSystemInfo) -> str:
        """Get Phison-named controller FW version.

        :param system_info: The controller's system information.
        :type system_info: phison_defs.PhisonSystemInfo
        :return: The FW version string.
        :rtype: str
        """
        return bytes(system_info.fw_ver).decode('ascii')


    @staticmethod
    def _is_security_access_enabled(system_info : phison_defs.PhisonSystemInfo) -> bool:
        """Determine if Security Access is enabled.

        :param system_info: The controller's system information.
        :type system_info: phison_defs.PhisonSystemInfo
        :return: Whether Security Access is enabled.
        :rtype: bool
        """
        security_level = system_info.security_level
        protection_state = system_info.protection_state

        if security_level != phison_defs.PhisonSecurityLevel.PHISON_SECURITY_LEVEL_DEFAULT.value:
            raise executor_exceptions.UnexpectedSecurityState(
                f"Unexpected security level {security_level}")

        if protection_state == \
            phison_defs.PhisonProtectionState.PHISON_PROTECTION_STATE_DEFAULT.value:
            return False


        if protection_state != \
            phison_defs.PhisonProtectionState.PHISON_PROTECTION_STATE_SECURITY_ACCESS_GRANTED.value:
            raise executor_exceptions.UnexpectedSecurityState(
                f"Unexpected protection state {protection_state}, try resetting the controller")

        return True


    def _get_system_info(self) -> phison_defs.PhisonSystemInfo:
        """Return the controller's system information.

        :return: The system information.
        :rtype: phison_defs.PhisonSystemInfo
        """
        system_info_size = ctypes.sizeof(phison_defs.PhisonSystemInfo)
        system_info_bytes = self._phison.phison_get_vsc_log_page(
            phison_defs.PhisonVSCLogPageId.PHISON_VSC_PAGE_ID_SYSTEM_INFO,
            0,
            system_info_size)

        system_info = phison_defs.PhisonSystemInfo.from_buffer_copy(system_info_bytes)

        return system_info


    def _install_server(self, server_binary : bytes, trampoline_binary : bytes):
        """Install the server binary into the controller.

        :param server_binary: The server binary bytes.
        :type server_binary: bytes
        :param trampoline_binary: The trampoline binary bytes.
        :type trampoline_binary: bytes
        """
        server_base_address = self._fw_defs['server_base_address']
        trampoline_address = self._fw_defs['server_trampoline_address']

        logger.info("Writing server binary...")
        self._phison_write_large(server_base_address, server_binary)

        logger.info("Writing server trampoline...")
        self._phison_write_large(trampoline_address, trampoline_binary)

        # Wait some time for data cache to be flushed
        # Not very reliable, but we don't have a call primitive
        # for cache flush at this point
        # @todo find a more reliable way.
        time.sleep(10)


    def _compute_key(self, decrypted_part : bytes) -> bytes:
        """Compute the response encryption key.

        :param decrypted_part: The decrypted part of the challenge.
        :type decrypted_part: bytes
        :return: The AES key to use for encrypting the response to controller.
        :rtype: bytes
        """
        decrypted_part_chunks = PhisonExecutor._split_to_key_size_chunks(
            decrypted_part)
        decrypted_part_xored = reduce(PhisonExecutor._xor_buffers,
                                      decrypted_part_chunks)

        modulus_bytes_chunks = PhisonExecutor._split_to_key_size_chunks(self._modulus_bytes)
        modulus_xor_result = reduce(PhisonExecutor._xor_buffers, modulus_bytes_chunks)

        return PhisonExecutor._xor_buffers(decrypted_part_xored, modulus_xor_result)


    def _generate_response(self, decrypted_part : bytes, plain_part : bytes) -> bytes:
        """Generate a response for the challenge to be sent to controller.

        :param decrypted_part: The decrypted part of the challenge.
        :type decrypted_part: bytes
        :param plain_part: The plain part of the challenge.
        :type plain_part: bytes
        :return: The encrypted challenge to send to the controller.
        :rtype: bytes
        """
        key = self._compute_key(decrypted_part)
        cipher = AES.new(key, AES.MODE_CBC, phison_defs.PHISON_SECURITY_AES_IV)
        return b''.join([cipher.encrypt(decrypted_part), plain_part])


    def _enable_security_access(self):
        """Enable Security Access on the target controller.
        """
        logger.info("Initiaing phase 1 -> 2 routine.")
        self._phison.phison_security_move_phase2(self._fw_defs['security_fw'])
        logger.info("Initiaing phase 2 -> 3 routine.")
        self._phison.phison_security_move_phase3()
        logger.info("Initiating phase 3 -> 4 routine.")
        challenge = self._phison.phison_security_move_phase4()
        encrypted_part_bytes = self._get_encrypted_challenge_part(challenge)
        plain_part_bytes = self._get_plain_challenge_part(challenge)
        decrypted_part_bytes = self._solve_rsa_challenge(encrypted_part_bytes[::-1])
        encrypted_response = self._generate_response(decrypted_part_bytes, plain_part_bytes)
        logger.info("Response generated. Sending response to controller (4 -> 5).")
        self._phison.phison_security_move_phase5(encrypted_response)
        logger.info("Security access granted.")


    def _solve_rsa_challenge(self, encrypted_part_bytes : bytes) -> bytes:
        """Decrypt the RSA-encrypted part of the challenge.

        :param encrypted_part_bytes: RSA-encrypted part from the challenge.
        :type encrypted_part_bytes: bytes
        :return: The decrypted data.
        :rtype: bytes

        .. note:: The encrypted part is in reverse order to what was received from
            the controller.
        """
        encrypted_part = bytes_to_long(encrypted_part_bytes)
        modulus = bytes_to_long(self._modulus_bytes)
        exp = bytes_to_long(self._exp_bytes)

        return long_to_bytes(pow(encrypted_part, exp, modulus))[::-1]


    def _phison_read_large(self, address : int, size : int) -> bytes:
        """Wrapper function for Phison VSC arbitrary read without a size limit.

        :param address: The address to start reading from.
        :type address: int
        :param size: The number of bytes to read.
        :type size: int
        :return: The bytes read.
        :rtype: bytes
        """
        read_data = b""
        chunk_size = phison_defs.PHISON_RW_CHUNK_SIZE

        for curr_offset in range(0, size, chunk_size):
            curr_read_size = min(chunk_size, size - curr_offset)
            read_data += self._phison.phison_memory_read(address + curr_offset, curr_read_size)

        return read_data


    def _phison_write_large(self, address : int, data : bytes):
        """Wrapper function for Phison VSC arbitrary write without a size limit.

        :param address: The address to start writing to.
        :type address: int
        :param data: The data to write.
        :type data: bytes
        """
        chunk_size = phison_defs.PHISON_RW_CHUNK_SIZE
        data_len = len(data)

        for curr_offset in range(0, data_len, chunk_size):
            curr_write_size = min(chunk_size, data_len - curr_offset)
            self._phison.phison_memory_write(
                address + curr_offset, data[curr_offset : ][: curr_write_size])


    def _issue_server_request(self, request : bytes) -> bytes:
        """Issue a request to the Server.

        :param request: The request bytes.
        :type request: bytes
        :raises phison_executor_defs.UnexpectedServerStatusException:
            A non-success status code returned from the Server.
        :return: The returned data from the Server.
        :rtype: bytes
        """
        request_response_address = self._fw_defs['server_request_response_address']
        self._phison_write_large(request_response_address, request)

        # Trigger server logic
        self._phison.phison_get_vsc_log_page(
            phison_defs.PhisonVSCLogPageId.PHISON_VSC_PAGE_ID_C6,
            0,
            0x1000
        )

        # Read Response (might be more than what's needed, maximum size is read for simplicity)
        response = self._phison_read_large(
            request_response_address, server_defs.MAX_SERVER_RESPONSE_SIZE)

        status, data = ServerInterface.parse_server_response(response)
        if status != server_defs.ServerStatus.SERVER_SUCCESS:
            raise executor_exceptions.UnexpectedServerStatusException(
                f"Unexpected status {status.value} returned from server!")

        return data


    def _is_server_up(self, server_binary : bytes) -> bool:
        """Determine if the server is up.

        :param server_binary: The server binary bytes.
        :type server_binary: bytes
        :return: Whether the server is up.
        :rtype: bool

        .. note:: Must be called after Security Access has been granted.
        """
        num_server_bytes_to_check = 0x10
        server_base_address = self._fw_defs['server_base_address']
        first_server_bytes = server_binary[ : num_server_bytes_to_check]

        return self._phison.phison_memory_read(server_base_address, num_server_bytes_to_check)\
              == first_server_bytes


    def memory_read(self, address : int, size : int) -> bytes:
        """Read arbitrary controller memory.

        :param address: The address to start reading from.
        :type address: int
        :param size: The number of bytes to read.
        :type size: int
        :raises ValueError: Non-positive read size value.
        :return: The bytes read.
        :rtype: bytes
        """
        if size <= 0:
            raise ValueError(f"Cannot have non-positive read size {size}")

        chunk_size = server_defs.MAX_READ_CHUNK_SIZE
        end_address = address + size
        read_data = b''

        for curr_address in range(address, address + size, chunk_size):
            curr_chunk_size = min(chunk_size, end_address - curr_address)
            read_data += self._issue_server_request(
                ServerInterface.build_read_memory_request(curr_address, curr_chunk_size))

        return read_data


    def memory_write(self, address : int, data : bytes):
        """Write arbitrary controller memory.

        :param address: The address to start writing to.
        :type address: int
        :param data: The data to write.
        :type data: bytes
        :raises ValueError: Empty data.
        """
        if len(data) == 0:
            raise ValueError("Cannot have empty data!")

         # @todo check that nobody writes on server/request memory.

        chunk_size = server_defs.MAX_WRITE_CHUNK_SIZE
        data_len = len(data)
        end_address = address + data_len

        for curr_offset in range(0, data_len, chunk_size):
            curr_chunk_size = min(chunk_size, end_address - curr_offset)
            write_data = data[curr_offset : ][ : curr_chunk_size]
            self._issue_server_request(
                ServerInterface.build_write_memory_request(address + curr_offset, write_data))


    def call_function(self,
                      address : int,
                      arg1 : int = 0,
                      arg2 : int = 0,
                      arg3 : int = 0,
                      arg4 : int = 0) -> int:
        """Call a function.

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
        :return: The 64-bit return value from the function.
        :rtype: bytes
        """
        return int.from_bytes(self._issue_server_request(
            ServerInterface.build_call_function_request(address, arg1, arg2, arg3, arg4)), 'little')


    def execute_shellcode(self, shellcode_binary_path : str) -> int:
        """Execute a shellcode binary on the controller.

        :param shellcode_binary_path: The path to the binary to execute.
        :type shellcode_binary_path: str
        :raises ValueError: Empty shellcode binary.
        :return: The 64-bit return value returned for the shellcode.
        :rtype: int
        """
        with open(shellcode_binary_path, 'rb') as f:
            shellcode_binary = f.read()

        shellcode_binary_len = len(shellcode_binary)
        if shellcode_binary_len == 0:
            raise ValueError("Empty shellcode provided!")

        self._issue_server_request(
            ServerInterface.build_initiate_data_transfer_request(shellcode_binary_len))

        chunk_size = server_defs.MAX_TRANSFER_CHUNK_SIZE

        for chunk_offset in range(0, shellcode_binary_len, chunk_size):
            chunk_end = min(shellcode_binary_len, chunk_offset + chunk_size)
            current_data_chunk = shellcode_binary[chunk_offset : chunk_end]

            # @todo maybe handle a possible exception in a more explicit manner?
            self._issue_server_request(
                ServerInterface.build_transfer_data_request(chunk_offset, current_data_chunk))

        return int.from_bytes(self._issue_server_request(
            ServerInterface.build_call_shellcode_request()), 'little')
