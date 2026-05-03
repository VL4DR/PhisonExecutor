import abc

class NVMEInterface(abc.ABC):

    @abc.abstractmethod
    def nvme_send_command(self, opcode : int, nsid : int, **kwargs : dict) -> tuple[int, bytes]:
        """Send an NVMe command to the controller.

		:param opcode: NVMe command code.
		:type opcode: int
		:param nsid: Namespace ID.
		:type nsid: int
		:raises ValueError: Invalid data or data length combination.
		:return: The ioctl return code and the NVMe buffer contents.
		:rtype: tuple[int, bytes]
		"""
