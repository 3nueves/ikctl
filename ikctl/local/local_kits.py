""" Module to Run kits in local servers """
import sys

from subprocess import run, PIPE

class RunLocalKits:
    """ Class to run kits in locals servers """

    def __init__(self, servers: dict, kits: list, exe: object, log: object, options: object) -> None:
        self.servers = servers
        self.kits = kits
        self.exe = exe
        self.log = log
        self.options = options
    
    def run_kits(self) -> None:
        """ Execute kits """

        if not self.options.name:
            print("\nName server not found, did you forgot --name option?")
            sys.exit()

        if self.kits is None:
            print("Kit not found")
            sys.exit()

        print(self.exe.run_local(self.options, self.kits))

        # return run([self.kits], shell=True, stdout=PIPE, check=True, universal_newlines=True, timeout=30) 