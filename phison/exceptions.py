class UnsupportedOSException(Exception):
    """The OS is unsupported.
	"""

class Phase2RecoverableException(Exception):
    """Security Access phase 2 expected and recoverable exception.
	"""


class Phase2UnexpectedException(Exception):
    """Security Access phase 2 unexpected exception.
	"""


class Phase3GeneralException(Exception):
    """Security Access phase 3 generic exception.
	"""


class Phase4GeneralException(Exception):
    """Security Access phase 4 generic exception.
	"""


class Phase5GeneralException(Exception):
    """Security Access phase 5 generic exception.
	"""


class InvalidSecurityResponseException(Exception):
    """Response to challenge was incorrect.
	"""


class PhisonVSCFailedException(Exception):
    """Generic exception indicating Phison VSC failure.
	"""
