""" Module to execute kit to remote server """
import logging
import re

import paramiko

class Commands:
    """ Class to exec kit to remote servers """

    log = ""
    check = ""
    client = ""
    logger = ""
    command = ""

    def __init__(self, command, client):

        self.command = command
        self.client = client

        self.logger = logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def ssh_run_command(self):
        """ execute script bash in remote server """

        try:
            self.logger.info(re.sub("echo (.*) \\|","echo ************ |",f'EXEC: {self.command}\n'))
            stdin, stdout, stderr = self.client.exec_command(self.command)

            stdout_lines = stdout.readlines()
            response = ''.join(stdout_lines)
            print(response)

            stderr_lines = stderr.readlines()
            errors = ''.join(stderr_lines)

            if errors:
                print("ERRORS\n")
                print(errors)
                print("END ERRORS")
            else:
                self.check = stdout.channel.recv_exit_status()

            return self.check, None, None

        except paramiko.SSHException as e:
            self.logger.error(e)

    def run_command(self):
        print("install local")