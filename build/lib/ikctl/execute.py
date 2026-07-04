""" class to build commands """
import os

from .logs import Log

class Exec:
    """ class to run the kits """
    def __init__(self, launch_remote_commands: object, logger: object) -> None:
        self.commands = launch_remote_commands
        self.log = Log()
        self.logger = logger

    def run_remote(self, conn, options, path, kit, mode, password):
        """ run the kits """
        # extract kit and path

        if mode == "command":
            command = self.commands(kit, conn.connection)

        elif options.sudo and options.parameter:
            command = self.commands("cd " + path + ";" + "echo "+password+" | sudo -S bash " + kit + " " + ' '.join(options.parameter), conn.connection)
            
        elif options.sudo and not options.parameter:
            command = self.commands("cd " + path + ";" + "echo "+password+" | sudo -S bash " + kit, conn.connection)
            
        elif not options.sudo and options.parameter:
            command = self.commands("cd " + path + ";" + "bash " + kit + " " + ' '.join(options.parameter), conn.connection)

        elif not options.sudo and not options.parameter:
            command = self.commands("cd " + path + ";" + "bash " + kit, conn.connection)
       
        command.ssh_run_command(self.logger)

        # return check, log, err

    def run_local(self, options, path_kits, password):
        """ run kits in local machine """

        path, kit = os.path.split(path_kits)

        if options.sudo and options.parameter:
            command = self.commands(f'cd {path}; echo {password} | sudo -S bash {kit} {" ".join(options.parameter)}')

        elif options.sudo and not options.parameter:
            command = self.commands(f'cd {path}; echo {password} | sudo -S bash {kit}')

        elif not options.sudo and options.parameter:
            command = self.commands(f"cd {path}; bash {kit} {' '.join(options.parameter)}")

        elif not options.sudo and not options.parameter:
            command = self.commands(f'cd {path}; bash {kit}')

        command.run_command()
