""" Module to install kits in remote servers """

import logging
import sys

from os import path

from .connect import Connection

class RunRemoteKits:
    """ Class to run kits in remote servers """

    def __init__(self, servers: dict, kits: list, sftp: object, exe: object, log: object, options: object) -> None:
        self.servers = servers
        self.kits = kits
        self.sftp = sftp
        self.exe = exe
        self.log = log
        self.logger = logging
        self.options = options
        self.kit_not_match = True

    # Run kits in remote servers
    def run_kits(self) -> None:
        """ Execute kits """

        if not self.options.name:
            print("\nName remote server not found, did you forgot --name option?")
            sys.exit()

        if self.kits is None:
            print("Kit not found")
            sys.exit()

        for host in self.servers['hosts']:
            conn = Connection(self.servers['user'], self.servers['port'], host, self.servers['pkey'], self.servers['password'])
            folder = self.sftp.list_dir(conn.connection_sftp, conn.user)
            # Create .ikctl folder in remote server
            if ".ikctl" not in folder:
                self.logger.info("Create folder ikctl")
                self.sftp.create_folder(conn.connection_sftp)

            print("###  Starting ikctl ###\n")

            self.logger.info('HOST: %s\n', conn.host)

            for local_kit in self.kits:
                # Destination route where we will upload the kits to the remote server
                remote_kit = ".ikctl/" + path.basename(local_kit)
                self.logger.info('UPLOAD: %s\n', remote_kit)
                self.sftp.upload_file(conn.connection_sftp, local_kit, remote_kit)
                self.kit_not_match = False
                    
            if ".sh" in remote_kit:
                check, log, err = self.exe.run(conn, self.options, remote_kit, "script", self.servers['password'])
                self.log.stdout(self.logger, log, err, check, level="DEBUG")

            self.logger.info(":END\n")

            conn.close_conn_sftp()