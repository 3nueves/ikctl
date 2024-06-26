""" Module to install kits in remote servers """

import logging
import sys

from os import path

from .connect import Connection

class RunRemoteKits:
    """ Class to run kits in remote servers """

    def __init__(self, servers: dict, name_kit: str, kits: list, pipe: list, sftp: object, exe: object, log: object, options: object) -> None:
        self.servers = servers
        self.name_kit = name_kit
        self.kits = kits
        self.pipe = pipe
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
        ## Loop servers
        for host in self.servers['hosts']:
            conn = Connection(self.servers['user'], self.servers['port'], host, self.servers['pkey'], self.servers['password'])
            # Create .ikctl folder in remote server
            folder = self.sftp.list_dir(conn.connection_sftp)
            if ".ikctl" not in folder:
                self.logger.info("Create folder ikctl")
                self.sftp.create_folder(conn.connection_sftp, ".ikctl")

            print("###  Starting ikctl ###\n")

            self.logger.info('HOST: %s\n', conn.host)

            # Get name of kit
            for nm_kit in self.name_kit['kits']:
                if self.options.install in nm_kit:
                    folder_kit = self.options.install

            for local_kit in self.kits:
                # Destination route where we will upload the kits to the remote server
                # folder_kit = path.basename(local_kit).replace(".sh", "")
                remote_kit = f".ikctl/{folder_kit}/{path.basename(local_kit)}"
                folder = self.sftp.list_dir(conn.connection_sftp, ".ikctl/")

                if folder_kit not in folder:
                    self.sftp.create_folder(conn.connection_sftp, ".ikctl/" + folder_kit)

                self.logger.info('UPLOAD: %s\n', remote_kit)
                self.sftp.upload_file(conn.connection_sftp, local_kit, remote_kit)
                self.kit_not_match = False
                    
            for cmd in self.pipe:
                route = path.dirname(remote_kit)
                kit = path.basename(cmd)
                check, log, err = self.exe.run_remote(conn, self.options, route, kit, "script", self.servers['password'])
                self.log.stdout(log, err, check)

            self.logger.info(":END\n")

            conn.close_conn_sftp()