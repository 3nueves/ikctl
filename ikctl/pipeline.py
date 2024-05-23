""" Module to launch one pipeline to install kits to the remote servers  """
import logging

from .logs import Log
from .view import Show
from .execute import Exec
from .config import Config
from .context import Context
from .remote.sftp import Sftp
from .commands import Commands
from .remote.run_kits import RunRemoteKits

class Pipeline:
    """ Class where we will initiation the process to install kits on remote servers """

    def __init__(self, options):

        self.options = options
        self.log = Log()
        self.sftp = Sftp()
        self.data = Config()
        self.logger = logging
        self.file = "ikctl.yaml"
        self.context = Context()
        self.exe = Exec(Commands)
        self.version = Config().version
        self.config_kits = self.data.load_config_file_kits()
        self.config_servers = self.data.load_config_file_servers()
        self.config_mode = self.data.load_config_file_mode()
        self.config_contexts = self.context.config
        self.view = Show(self.config_kits, self.config_servers, self.config_contexts)
        self.servers = self.data.extract_config_servers(self.config_servers, self.options.name)
        self.kits = self.data.extrac_config_kits(self.config_kits, self.options.install)
        self.run_remote_kits = RunRemoteKits(self.servers, self.kits, self.sftp, self.exe, self.log, self.options)
        self.init()

    def init(self):
        """ Function to initiation pipeline """

        self.logger = logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Manage context
        if self.options.context:
            self.context.change_context(self.options.context)
        
        # Show configuration
        if self.options.list:
            self.view.show_config(self.options.list)
        
        # Install kits in servers
        if self.options.install:

            # Run kits in local machine
            if self.config_mode == 'local':
                print("local")

            # Run kits in remote servers
            if self.config_mode == 'remote':
                self.run_remote_kits.run_kits()