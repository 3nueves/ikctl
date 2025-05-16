""" Module to execute kit to remote server """
import logging
import re

from subprocess import run

import paramiko
from .logs import Log


class Commands:
    """ Class to exec kit in remote and locals servers """

    def __init__(self, command, client=None):
        name = __name__.split(".")
        self.name = name[-1]
        self.command = command
        self.client = client
        self.log = Log()
        self.logger = logging.getLogger(self.name)

    def ssh_run_command(self, logger):
        """ execute script bash in remote server """

        try:
            logger.info(re.sub("echo (.*) \\|", "echo ************ |", f'EXEC: {self.command}'))
            stdin, stdout, stderr = self.client.exec_command(self.command)

            for log in stdout:
                print(f"\033[1;32m{log.strip()}")

            for log in stderr:
                print(f"\x1b[31;1m{log.strip()}")

            self.log.stdout(None, None, stdout.channel.recv_exit_status())

        except paramiko.SSHException as e:
            logger.error(e)

    def run_command(self):
        """ run kits in local machine """

        self.logger.info(f"EXEC: {re.sub("echo (.*) \\|", "echo ************ |", self.command)}")

        data = run([self.command], shell=True, text=True, capture_output=True, timeout=30)

        self.log.stdout(data.stdout, data.stderr, data.returncode)
