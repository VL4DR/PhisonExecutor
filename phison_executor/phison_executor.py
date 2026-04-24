import time
import logging
from functools import reduce
from Crypto.Cipher import AES
from Crypto.Util.number import bytes_to_long, long_to_bytes
import phison_executor.phison_executor_defs as phison_executor_defs
import phison.phison_defs as phison_defs
from phison.phison_layer import PhisonLayer

logger = logging.getLogger(__name__)

class PhisonExecutor:

    def __init__(self, device_path : str, server_binary_path : str):
        self._phison = PhisonLayer(device_path)
        fw_version = self._get_fw_version()
        if not fw_version in phison_executor_defs.PHISON_EXECUTOR_DEFS:
            raise phison_executor_defs.FirmwareUnsupportedException(f"FW version {fw_version} is currently unsupported!")
        
        self._fw_defs = phison_executor_defs.PHISON_EXECUTOR_DEFS[fw_version]

        with open(self._fw_defs['modulus_path'], 'rb') as f:
            self._modulus_bytes = f.read()

        with open(self._fw_defs['exp_path'], 'rb') as f:
            self._exp_bytes = f.read()

        self._enable_security_access()
        self._install_server(server_binary_path)

    @staticmethod
    def _get_plain_challenge_part(challenge_data : bytes):
        assert len(challenge_data) == phison_defs.PHISON_SECURITY_CHALLENGE_SIZE
        return challenge_data[phison_defs.PHISON_SECURITY_CHALLENGE_ENCRYPTED_PART_SIZE : ]
    
    @staticmethod
    def _xor_buffers(buffer_a : bytes, buffer_b : bytes):
        assert len(buffer_a) == len(buffer_b)
        return bytes([buffer_a[i] ^ buffer_b[i] for i in range(len(buffer_a))])
    
    @staticmethod
    def _split_to_key_size_chunks(some_bytes : bytes):
        lst = []
        for i in range(0, len(some_bytes), phison_defs.PHISON_SECURITY_AES_KEY_SIZE):
            lst.append(some_bytes[i : i + phison_defs.PHISON_SECURITY_AES_KEY_SIZE])
            
        return lst
    
    def _get_fw_version(self):
        return "EIFK51.2"


    def _install_server(self):
        with open(self._fw_defs['server_binary_path'], 'rb') as f:
            server_binary = f.read()

        with open(self._fw_defs['server_trampoline_binary_path'], 'rb') as f:
            trampoline_binary = f.read()

        server_base_address = self._fw_defs['server_base_address']
        trampoline_address = self._fw_defs['server_trampoline_address']

        # Write server binary
        self.memory_write(server_base_address, server_binary)

        # And now the trampoline that points to it
        self.memory_write(trampoline_address, trampoline_binary)

        # Wait some time for data cache to be flushed
        # Not very reliable, but we don't have a call primitive
        # for cache flush at this point
        time.sleep(10)
    
    
    def _compute_key(self, reconstructed_sequence : bytes):
        reconstructed_sequence_chunks = PhisonExecutor._split_to_key_size_chunks(reconstructed_sequence)
        reconstructed_result = reduce(lambda x, y: PhisonExecutor._xor_buffers(x, y), reconstructed_sequence_chunks)
        
        secret_bytes_chunks = PhisonExecutor._split_to_key_size_chunks(self._modulus_bytes)
        secret_result = reduce(lambda x, y: PhisonExecutor._xor_buffers(x, y), secret_bytes_chunks)
        
        return PhisonExecutor._xor_buffers(reconstructed_result, secret_result)
    
    def _generate_response(self, reconstructed_challenge : bytes):
        scrambled_part_size = phison_defs.PHISON_SECURITY_CHALLENGE_ENCRYPTED_PART_SIZE
        reconstructed_part = reconstructed_challenge[ : scrambled_part_size]
        
        key = self._compute_key(reconstructed_part)
        cipher = AES.new(key, AES.MODE_CBC, phison_defs.PHISON_SECURITY_AES_IV)
        return cipher.encrypt(reconstructed_part) + PhisonExecutor._get_plain_challenge_part(reconstructed_challenge)
        
    def _enable_security_access(self):
        logger.info("Initiaing phase 1 -> 2 routine.")
        self._phison.phison_security_move_phase2(self._fw_defs['security_fw'])
        logger.info("Initiaing phase 2 -> 3 routine.")
        self._phison.phison_security_move_phase3()
        logger.info("Initiating phase 3 -> 4 routine.")
        challenge = self._phison.phison_security_move_phase4()
        encrypted_part_bytes = challenge[ : phison_defs.PHISON_SECURITY_CHALLENGE_ENCRYPTED_PART_SIZE][::-1]
        decrypted_part_bytes = self._solve_rsa_challenge(encrypted_part_bytes)
        plain_response = b''.join([decrypted_part_bytes, challenge[phison_defs.PHISON_SECURITY_CHALLENGE_ENCRYPTED_PART_SIZE : ]])
        encrypted_response = self._generate_response(plain_response, modulus_bytes)
        logger.info("Response generated. Sending response to controller (4 -> 5).")
        self._phison.phison_security_move_phase5(encrypted_response)
        logger.info("Security access granted.")

    def _solve_rsa_challenge(self, encrypted_part_bytes : bytes) -> bytes:
        
        encrypted_part = bytes_to_long(encrypted_part_bytes)
        modulus = bytes_to_long(self._modulus_bytes)
        exp = bytes_to_long(self._exp_bytes)

        return long_to_bytes(pow(encrypted_part, exp, modulus))[::-1]


    def memory_read(self, address : int, size : int, core : int = 0):
        return self._phison.phison_memory_read(address, size, core)
    
    def memory_write(self, address : int, data : bytes, core : int = 0):
        self._phison.phison_memory_write(address, data)
    
    def execute_shellcode(self, shellcode_binary_path : str):
        with open(shellcode_binary_path, 'rb') as f:
            shellcode_binary = f.read()

        if len(shellcode_binary) == 0:
            raise ValueError("Empty shellcode provided!")
        
