from abc import abstractmethod
from abc import ABCMeta

class kits(metaclass=ABCMeta):
    @abstractmethod
    def run_kits(self):
        pass
