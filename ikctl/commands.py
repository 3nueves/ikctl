""" Module to execute kit to remote server """
import logging
import re

import paramiko

from subprocess import run, PIPE

class Commands:
    """ Class to exec kit in remote and locals servers """

    log = ""
    check = ""
    client = ""
    logger = ""
    command = ""

    def __init__(self, command, client=None):

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

            stderr_lines = stderr.readlines()

            if not stderr_lines:
                self.check = stdout.channel.recv_exit_status()

            return self.check, response, stderr_lines

        except paramiko.SSHException as e:
            self.logger.error(e)

    def run_command(self):
        """ run kits in local machine """
        print("\033[94m")
        print(f"{re.sub("echo (.*) \\|","echo ************ |",self.command)}")
        return run([self.command], shell=True, text=True, capture_output=True, timeout=30)