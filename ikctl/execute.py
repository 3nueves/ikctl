from commands import Commands

class Exec:
    def __init__(self) -> None:
        pass

    def run(self, conn, options, commands, mode, password):

        if mode == "command":
            command = Commands(commands, conn.connection)

        elif options.sudo and options.parameter:
            command = Commands("echo "+password+" | sudo -S bash " + commands + " " + options.parameter, conn.connection)
            # command = Commands("sudo bash " + commands + " " + options.parameter, conn.connection)
            
        elif options.sudo and not options.parameter:
            command = Commands("echo "+password+" | sudo -S bash " + commands, conn.connection)
            # command = Commands("sudo bash " + commands, conn.connection)
            
        elif not options.sudo and options.parameter:
            command = Commands("bash " + commands + " " + options.parameter, conn.connection)

        elif not options.sudo and not options.parameter:
            command = Commands("bash " + commands, conn.connection)
        
        check, log, err = command.ssh_run_command()

        return check, log, err