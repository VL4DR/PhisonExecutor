class DeviceInaccessibleException(Exception):
    """Target device is not accessible.
	"""

class InternalFunctionFailureException(Exception):
    """Internal function call failed.
    """

class NVMEFwCommitException(Exception):
    """NVMe Commit failure.
    """

class NVMEFwDownloadException(Exception):
    """NVMe download failure.
    """

class UnsupportedOSException(Exception):
    """OS is unsupported.
    """
