PHISON_EXECUTOR_RW_CHUNK_SIZE = 0x1000

ECFM322_DEFS = {
    'security_fw' : 'resources/ECFM32.2/security_fw.bin',
	'modulus_path' : 'resources/ECFM32.2/modulus.bin',
	'exp_path' : 'resources/ECFM32.2/exp.bin',
	'server_binary_path' : 'resources/ECFM32.2/server.bin',
    'server_base_address' : 0,
    'server_trampoline_binary_path' : 'resources/ECFM32.2/trampoline.bin',
    'server_trampoline_address' : 0
}

EIFK512_DEFS = {
    'security_fw' : 'resources/EIFK51.2/security_fw.bin',
    'modulus_path' : 'resources/EIFK51.2/modulus.bin',
	'exp_path' : 'resources/EIFK51.2/exp.bin',
    'server_binary_path' : 'resources/EIFK51.2/server.bin',
    'server_base_address' : 0x4016A000,
    'server_trampoline_binary_path' : 'resources/EIFK51.2/trampoline.bin',
    'server_trampoline_address' : 0x40151D38
}

EIFM800_DEFS = {
    'security_fw' : 'resources/EIFM80.0/security_fw.bin',
	'modulus_path' : 'resources/EIFM80.0/modulus.bin',
	'exp_path' : 'resources/EIFM80.0/exp.bin',
    'server_binary_path' : 'resources/EIFM80.0/server.bin',
    'server_base_address' : 0,
    'server_trampoline_binary_path' : 'resources/EIFM80.0/trampoline.bin',
    'server_trampoline_address' : 0
}

PHISON_EXECUTOR_DEFS = {
	'EIFK51.2' : EIFK512_DEFS,
	'ECFM32.2' : ECFM322_DEFS,
	'EIFM80.0' : EIFM800_DEFS,
}

class FirmwareUnsupportedException(Exception):
    pass

class ChallengeFailedException(Exception):
    pass
