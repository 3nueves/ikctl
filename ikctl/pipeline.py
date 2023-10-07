import logging
from logs import Log
from view import Show
from sftp import Sftp
from execute import Exec
from config import Config
from connect import Connection


class Pipeline:


    def __init__(self):

        self.path = []
        self.files = []
        self.log = Log()
        self.exe = Exec()
        self.view = Show()
        self.sftp = Sftp()
        self.data = Config()
        self.connection = []
        self.logger = logging
        self.file = "ikctl.yaml"
        self.kit_not_match = True
        self.config_kits = self.data.load_config_file_kits()
        self.config_servers = self.data.load_config_file_servers()

    def init(self, options):

        self.logger = logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # load servers
        user, port, pkey, hosts, password = self.data.extract_config_servers(self.config_servers, options.name)

        # load kit
        kit = self.data.extrac_config_kits(self.config_kits, options.name)

        # show configuration
        if options.list:
            self.view.show_config(options.list)

        # init install
        if options.install:

            # Create path to scripts
            for co in config["kits"]:
                c = self.data.load_config(path_ikctl["kits"]+co)
                for file in c["kits"]:
                    path = co.replace("ikctl.yaml", file)
                    self.path.append(path_ikctl["kits"]+path)
                    self.files.append(file)

            # Upload scripts
            for host in hosts:
                conn = Connection(user, port, host, pkey, password)
                folder = self.sftp.list_dir(conn.connection_sftp, conn.user)
                if ".ikctl" not in folder:
                    self.logger.info(f"Create folder ikctl")
                    self.sftp.create_folder(conn.connection_sftp)

                c = -1
                for script in self.path:
                    script_local = script
                    c += 1
                    script_remote = ".ikctl/" + self.files[c]
                    if options.install in script_local:
                        print()
                        self.logger.info(f'HOST: {conn.host}\n')
                        self.logger.info(f'UPLOAD: {script_remote}\n')
                        self.sftp.upload_file(
                            conn.connection_sftp, script_local, script_remote
                        )
                        self.kit_not_match = False
                        
                        if ".sh" in script_remote:
                            check, log, err = self.exe.run(conn, options, script_remote, "script", password)
                            self.log.stdout(self.logger, log, err, check, level="DEBUG")

                        self.logger.info(":END\n")

                conn.close_conn_sftp()

            if self.kit_not_match:
                print("Kit not found in ikctl")