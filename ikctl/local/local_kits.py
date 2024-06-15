""" Module to Run kits in local servers """
import logging
import sys

class RunLocalKits:
    """ Class to run kits in locals servers """

    def __init__(self, servers: dict, kits: list, exe: object, log: object, options: object) -> None:
        self.servers = servers
        self.kits = kits
        self.exe = exe
        self.log = log
        self.options = options
        self.logger = logging
    
    def run_kits(self) -> None:
        """ Execute kits """

        if self.kits is None:
            print("Kit not found")
            sys.exit()

        check, log, err  = self.exe.run_local(self.options, self.kits, self.servers['password'])
        self.log.stdout(log, err, check)