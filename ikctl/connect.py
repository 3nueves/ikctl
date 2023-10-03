import logging
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

            if self.pkey:
                private_key = paramiko.RSAKey.from_private_key_file(self.pkey)

            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if not self.pkey:
                client.connect(
                    self.host, port=self.port, username=self.user, password=self.password, timeout=500
                )
            else:
                client.connect(
                    self.host, port=self.port, username=self.user, pkey=private_key, timeout=500
                )

            self.connection = client
            self.connection_sftp = client.open_sftp()


        except paramiko.SSHException as e:
            self.logger.error(e)
            # print(e)
    

    def close_conn(self):
        self.connection.close()

    def close_conn_sftp(self):
        self.connection_sftp.close()
