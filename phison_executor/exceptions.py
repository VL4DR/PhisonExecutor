class FirmwareUnsupportedException(Exception):
    """Firmware version is not supported.
    """


class UnexpectedServerStatusException(Exception):
    """Unexpected status returned from Server.
    """


class UnexpectedSecurityState(Exception):
    """Unexpected controller security state.
    """
