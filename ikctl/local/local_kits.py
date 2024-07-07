""" Module to Run kits in local servers """
import logging

class RunLocalKits:
    """ Class to run kits in locals servers """

    def __init__(self, servers: dict, kits: list, pipe: list, exe: object, log: object, options: object) -> None:

        name = __name__.split(".")
        self.name = name[-1]
        self.servers = servers
        self.kits = kits
        self.pipe = pipe
        self.exe = exe
        self.log = log
        self.options = options
        self.logger = logging.getLogger(self.name)
    
    def run_kits(self) -> None:
        """ Execute kits """

        if self.kits is None:
            self.logger.warning("Kit not found")
            exit()

        print()
        self.logger.info("Starting")
        
        for cmd in self.pipe:
            self.exe.run_local(self.options, cmd, self.servers['password'])
            
        self.logger.info(":END")