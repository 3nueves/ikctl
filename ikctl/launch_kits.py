from abc import abstractmethod
from abc import ABCMeta

class LaunchKits(metaclass=ABCMeta):
    @abstractmethod
    def run_kits(self):
        pass
