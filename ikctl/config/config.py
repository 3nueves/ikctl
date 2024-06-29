""" Module to load configuration """
import pathlib
import os
import sys
from envyaml import EnvYAML
from .create_config_files import CreateFolderAndConfigFile

__version__ = "v0.3.0"

class Config():
    """ Manage path kits """

    def __init__(self):
        self.config = ""
        self.version = __version__
        self.home = pathlib.Path.home()
        self.path_config_file = self.home.joinpath('.ikctl/config')
        self.create_config_file = CreateFolderAndConfigFile()
        self.__create_folder_and_config_file()
        self.__load_config_file_where_are_kits()
        self.context = self.config['context']


    def __create_folder_and_config_file(self):
        """ Create Config file and folder """
        self.create_config_file.create_folder()
        self.create_config_file.create_config_file()


    def __load_config_file_where_are_kits(self):
        """ Load Config ikctl """
        try:
            self.config = EnvYAML(self.path_config_file, strict=False)

        except ValueError as error:
            print(f'\n--- {error} ---\n')
            sys.exit()

        except Exception as e:
            # print(f"\nERROR IN FILE: {self.path_config_file}\n\n", e)
            print("\n",e)
            sys.exit()

        return self.config

    def load_config_file_mode(self):
        """ Load Mode """

        try:
            return (self.config['contexts'][self.context]['mode'])

        except (ValueError, KeyError) as error:
            print(f'\n keyError: {error} has a mistake\n')
            sys.exit()

    def load_config_file_kits(self):
        """ Load kits """

        try:
            kits = (self.config['contexts'][self.context]['path_kits'])

        except (ValueError, KeyError) as error:
            print(f'\n keyError: {error} has a mistake\n')
            sys.exit()

        try:
            kit = EnvYAML(kits + "/ikctl.yaml")
            if kit.get("kits"):
                return kit
            else:
                print(f"\nERROR IN FILE: {kits}/ikctl.yaml\n")
                sys.exit()

        except (ValueError, KeyError):
            print(f'\n KeyError: {error} there is a mistake\n')
            sys.exit()

        except Exception as e:
            print()
            print("[ikctl - kits configs]",e,"\n")
            sys.exit()
        

    def load_config_file_servers(self):
        """ Load Hosts """

        try:
            servers = (self.config['contexts'][self.context]['path_servers'])
        
        except (ValueError, KeyError) as error:
            print(f'\n keyError: {error} has a mistake\n')
            sys.exit()

        try:
            return EnvYAML(servers + "/config.yaml")

        except (ValueError) as error:
            print(f'\n--- {error} ---\n')
            sys.exit()

        except Exception as e:
            print()
            print("[ikctl - servers config]",e,"\n")
            sys.exit()
            sys.exit()


    def extract_config_servers(self, config, group=None):
        """ Extract values from config file """
        hosts = []

        for m in config["servers"]:
            if group == m["name"]:
                user     = m.get("user", "kub")
                port     = m.get("port", 22)
                password = m.get("password", "no_pass")
                pkey     = m.get("pkey", None)
                if m.get("hosts", None):
                    hosts = [host for host in m['hosts']]
            elif group is None:
                user     = m.get("user", "kub")
                port     = m.get("port", 22)
                password = m.get("password", "no_pass")
                pkey     = m.get("pkey", None)
                if m.get("hosts", None):
                    hosts = [host for host in m['hosts']]
        if not hosts:
            print("Host not found")
            sys.exit()

        data = {
            'user': user,
            'port': port,
            'pkey': pkey,
            'hosts': hosts,
            'password': password
        }

        return data
        # return user, port, pkey, hosts, password

    def extrac_config_kits(self, config, name_kit):
        """ Extract values from config file """
        uploads = []
        pipeline = []

        # Route where the kits are located
        path_kits = self.config['contexts'][self.context]['path_kits']

        # We tour the cars that we have extracted from above
        for kit in config['kits']:

            # Buscamos la coincidencia con el kit que deseamos
            if name_kit == os.path.dirname(kit):

                # Generamos las rutas hasta donde están los kits
                # para poder subirlos a los servidores
                path_until_folder = os.path.dirname(path_kits + "/" + kit)
                object_with_path = EnvYAML(path_kits + "/" + kit)

                # Append all kits that we want upload
                for upload in object_with_path["kits"]["uploads"]:
                    uploads.append(path_until_folder + "/" + upload)

                # Append the kits that we are running 
                for pipe in object_with_path['kits']['pipeline']:
                    pipeline.append(path_until_folder + "/" + pipe)

                if uploads is None:
                    print("Kit not found")
                    sys.exit()
                else:
                    return uploads, pipeline
