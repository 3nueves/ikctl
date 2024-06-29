""" Module to Run kits in local servers """
import logging

class RunLocalKits:
    """ Class to run kits in locals servers """

    def __init__(self, servers: dict, kits: list, pipe: list, exe: object, log: object, options: object) -> None:
        self.servers = servers
        self.kits = kits
        self.pipe = pipe
        self.exe = exe
        self.log = log
        self.options = options
        self.logger = logging
    
    def run_kits(self) -> None:
        """ Execute kits """

        if self.kits is None:
            print("Kit not found")
            exit()
        for cmd in self.pipe:
            stdout, stderr, returncode = self.exe.run_local(self.options, cmd, self.servers['password'])
            self.log.stdout(stdout, stderr, returncode)