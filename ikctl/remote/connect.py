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
        self.logger.getLogger("paramiko").setLevel(logging.WARN)

        self.open_conn()

    def open_conn(self):
        """ Create ssh connection """
        # if not self.pkey:
        #     password = getpass("input your password: ")

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.pkey:
                private_key = paramiko.RSAKey.from_private_key_file(self.pkey)
                client.connect(self.host, port=self.port, username=self.user, pkey=private_key, timeout=500)
                
            elif self.password != "no_pass":
                self.password = "no_pass"
                client.connect(self.host, port=self.port, username=self.user, password=self.password, allow_agent=False, look_for_keys=False, timeout=500)

        except FileNotFoundError as e:
            print("\x1b[31;1m")
            self.logger.error(f'{e}\n')
            print("\x1b[0m")
            sys.exit()

        except paramiko.SSHException as e:
            print("\x1b[31;1m")
            self.logger.error(f"{e}")
            print("\x1b[0m")

            if self.password != "no_pass":

                try:
                    self.logger.info("Authentication with ssh key failed, trying to connect with password instead ssh key.\n")
                    client.connect(self.host, port=self.port, username=self.user, password=self.password, allow_agent=False, look_for_keys=False, timeout=500)

                except FileNotFoundError as error:
                    print("\x1b[31;1m")
                    self.logger.error(f'{error}\n')
                    print("\x1b[0m")
                    sys.exit()

                except paramiko.SSHException as error:
                    print("\x1b[31;1m")
                    self.logger.error(f"{error}\n")
                    print("\x1b[0m")
                    sys.exit()
                    
                else:
                    self.connection = client
                    self.connection_sftp = client.open_sftp()

            else:
                sys.exit()
        else:
            self.connection = client
            self.connection_sftp = client.open_sftp()

    def close_conn(self):
        """ close ssh connection """

        self.connection.close()

    def close_conn_sftp(self):
        """ close sftp connection """

        self.connection_sftp.close()
