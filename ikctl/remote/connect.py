"""
Module to make connection ssh to remote servers 
"""
import logging
import sys
import paramiko
from getpass import getpass


class Connection:

    user = ""
    port = ""
    host = ""
    pkey = ""
    connection = ""

    def __init__(self, user, port, host, pkey, password):
        self.user     = user
        self.port     = port
        self.host     = host
        self.pkey     = pkey
        self.password = password

        self.logger = logging
        self.logger.basicConfig()
        self.logger.getLogger("paramiko").setLevel(logging.WARNING)

        self.open_conn()

    def open_conn(self):

        # if not self.pkey:
        #     password = getpass("input your password: ")

        try:
            client = paramiko.SSHClient()

            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.pkey:
                private_key = paramiko.RSAKey.from_private_key_file(self.pkey)
                client.connect(self.host, port=self.port, username=self.user, pkey=private_key, timeout=500)

            if self.password != "no_pass":
                client.connect(self.host, port=self.port, username=self.user, password=self.password, allow_agent=False, look_for_keys=False, timeout=500)


            self.connection = client
            self.connection_sftp = client.open_sftp()


        except (paramiko.SSHException, FileNotFoundError) as e:
        # except FileNotFoundError as e:
            print()
            self.logger.error(f'{e}\n')
            sys.exit()
    

    def close_conn(self):
        self.connection.close()

    def close_conn_sftp(self):
        self.connection_sftp.close()
