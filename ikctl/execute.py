# from .commands import Commands

class Exec:
    """ class to run the kits """
    def __init__(self, launch_remote_commands: object) -> None:
        self.commands = launch_remote_commands

    def run(self, conn, options, commands, mode, password):
        """ run the kits """
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