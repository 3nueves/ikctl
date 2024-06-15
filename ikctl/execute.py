# from .commands import Commands
import os
class Exec:
    """ class to run the kits """
    def __init__(self, launch_remote_commands: object) -> None:
        self.commands = launch_remote_commands

    def run_remote(self, conn, options, commands, mode, password):
        """ run the kits """

        path, kit = os.path.split(commands)

        print(path)
        print(kit)

        if mode == "command":
            command = self.commands(commands, conn.connection)

        elif options.sudo and options.parameter:
            command = self.commands("echo "+password+" | sudo -S bash " + commands + " " + ' '.join(options.parameter), conn.connection)
            
        elif options.sudo and not options.parameter:
            command = self.commands("echo "+password+" | sudo -S bash " + commands, conn.connection)
            
        elif not options.sudo and options.parameter:
            command = self.commands("bash " + commands + " " + ' '.join(options.parameter), conn.connection)

        elif not options.sudo and not options.parameter:
            command = self.commands("bash " + commands, conn.connection)
       
        check, log, err = command.ssh_run_command()

        return check, log, err

    def run_local(self, options, path_kits, password):
        """ run kits in local machine """

        path, kit = os.path.split(' '.join(path_kits))

        if options.sudo and options.parameter:
            command = self.commands(f'cd {path}; echo {password} | sudo -S bash {kit} {" ".join(options.parameter)}')

        elif options.sudo and not options.parameter:
            command = self.commands(f'cd {path}; echo {password} | sudo -S bash {kit}')

        elif not options.sudo and options.parameter:
            command = self.commands(f'cd {path}; bash {kit} {' '.join(options.parameter)}')

        elif not options.sudo and not options.parameter:
            command = self.commands(f'cd {path}; bash {kit}')
       
        data = command.run_command()

        return data.returncode, data.stdout, data.stderr
