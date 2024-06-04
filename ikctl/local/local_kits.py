""" Module to Run kits in local servers """
import sys

class RunLocalKits:
    """ Class to run kits in locals servers """

    def __init__(self, servers: dict, kits: list, log: object, options: object) -> None:
        self.servers = servers
        self.kits = kits
        self.log = log
        self.options = options
    
    def run_kits(self) -> None:
        """ Execute kits """

        if not self.options.name:
            print("\nName remote server not found, did you forgot --name option?")
            sys.exit()

        if self.kits is None:
            print("Kit not found")
            sys.exit() 
        
        print(self.kits)