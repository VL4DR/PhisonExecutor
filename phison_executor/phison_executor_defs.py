ECFM322_DEFS = {
    'security_fw' : 'resources/ECFM32.2/security_fw.bin',
	'modulus_path' : 'resources/ECFM32.2/modulus.bin',
	'exp_path' : 'resources/ECFM32.2/exp.bin',
	'server_binary_path' : 'resources/ECFM32.2/server.bin',
    'server_base_address' : 0x4016A000,
    'server_trampoline_binary_path' : 'resources/ECFM32.2/trampoline.bin',
    'server_trampoline_address' : 0x4011B84E,
    'server_request_response_address' : 0x4016B000
}


EGFM132_DEFS = {
    'security_fw' : 'resources/EGFM13.2/security_fw.bin',
	'modulus_path' : 'resources/EGFM13.2/modulus.bin',
	'exp_path' : 'resources/EGFM13.2/exp.bin',
	'server_binary_path' : 'resources/EGFM13.2/server.bin',
    'server_base_address' : 0, # @todo fill correct value
    'server_trampoline_binary_path' : 'resources/EGFM13.2/trampoline.bin',
    'server_trampoline_address' : 0, # @todo fill correct value
    'server_request_response_address' : 0 # @todo fill correct value
}


EIFK512_DEFS = {
    'security_fw' : 'resources/EIFK51.2/security_fw.bin',
    'modulus_path' : 'resources/EIFK51.2/modulus.bin',
	'exp_path' : 'resources/EIFK51.2/exp.bin',
    'server_binary_path' : 'resources/EIFK51.2/server.bin',
    'server_base_address' : 0x4016A000,
    'server_trampoline_binary_path' : 'resources/EIFK51.2/trampoline.bin',
    'server_trampoline_address' : 0x40151D38,
    'server_request_response_address' : 0x4016B000
}


EIFM800_DEFS = {
    'security_fw' : 'resources/EIFM80.0/security_fw.bin',
	'modulus_path' : 'resources/EIFM80.0/modulus.bin',
	'exp_path' : 'resources/EIFM80.0/exp.bin',
    'server_binary_path' : 'resources/EIFM80.0/server.bin',
    'server_base_address' : 0x4016A000,
    'server_trampoline_binary_path' : 'resources/EIFM80.0/trampoline.bin',
    'server_trampoline_address' : 0x40153230,
    'server_request_response_address' : 0x4016B000
}


PHISON_EXECUTOR_DEFS = {
    'ECFM32.2' : ECFM322_DEFS,
    'EGFM13.2' : EGFM132_DEFS,
	'EIFK51.2' : EIFK512_DEFS,
	'EIFM80.0' : EIFM800_DEFS,
}


# The chunk size used by the Executor when doing large reads/writes.
PHISON_EXECUTOR_RW_CHUNK_SIZE = 0x1000


class FirmwareUnsupportedException(Exception):
    """Firmware version is not supported.
    """


class UnexpectedServerStatusException(Exception):
    """Unexpected status returned from Server.
    """
