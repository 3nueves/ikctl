""" Module to launch one pipeline to install kits to the remote servers  """
import logging
import sys

from os import path

from .logs import Log
from .view import Show
from .sftp import Sftp
from .execute import Exec
from .config import Config
from .connect import Connection
from .context import Context

class Pipeline:
    """ Class where we will initiation the process to install kits on remote servers """

    def __init__(self):

        self.path = []
        self.files = []
        self.log = Log()
        self.exe = Exec()
        self.sftp = Sftp()
        self.data = Config()
        self.connection = []
        self.logger = logging
        self.file = "ikctl.yaml"
        self.kit_not_match = True
        self.context = Context()
        self.config_kits = self.data.load_config_file_kits()
        self.config_servers = self.data.load_config_file_servers()
        self.config_contexts = self.context.config
        self.view = Show(self.config_kits, self.config_servers, self.config_contexts)

    def init(self, options):
        """ Function to initiation pipeline """

        self.logger = logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Load server
        user, port, pkey, hosts, password = self.data.extract_config_servers(self.config_servers, options.name)

        # Manage context
        if options.context:
            self.context.change_context(options.context)
                
        # Show configuration
        if options.list:
            self.view.show_config(options.list)

        # Install kits in servers
        if options.install:

            # Load kit
            kits = self.data.extrac_config_kits(self.config_kits, options.install)
            if kits is None:
                print("Kit not found")
                sys.exit()

        for host in hosts:
            conn = Connection(user, port, host, pkey, password)
            folder = self.sftp.list_dir(conn.connection_sftp, conn.user)
            if ".ikctl" not in folder:
                self.logger.info("Create folder ikctl")
                self.sftp.create_folder(conn.connection_sftp)

            print("###  Starting ikctl ###\n")

            self.logger.info('HOST: %s\n', conn.host)

            for local_kit in kits:
                # Destination route where we will upload the kits to the remote server
                remote_kit = ".ikctl/" + path.basename(local_kit)
                self.logger.info('UPLOAD: %s\n', remote_kit)
                self.sftp.upload_file(conn.connection_sftp, local_kit, remote_kit)
                self.kit_not_match = False
                    
            if ".sh" in remote_kit:
                check, log, err = self.exe.run(conn, options, remote_kit, "script", password)
                self.log.stdout(self.logger, log, err, check, level="DEBUG")

            self.logger.info(":END\n")

            conn.close_conn_sftp()
