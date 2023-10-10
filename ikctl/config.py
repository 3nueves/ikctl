# 1.- Cargar archivo desde la $HOME/.ikctl
# 2.- Comprobar que existe el directorio $HOME/.ikctl
# 3.- Si no existe avisar que no existe
# 5.- Si existe el fichero cargarlo y retornarlo

import pathlib
import os
import sys
import yaml
from yaml.loader import SafeLoader
from envyaml import EnvYAML
from create_config_files import CreateFolderAndConfigFile

class Config():
    """
    Manage path where are kits

    var:
        change_context => Value to change context
    """

    def __init__(self, change_context=None):
        self.config = ""
        self.change_context = change_context
        self.home = pathlib.Path.home()
        self.path_config_file = self.home.joinpath('.ikctl/config')
        self.create_config_file = CreateFolderAndConfigFile()
        self.__create_folder_and_config_file()
        self.__load_config_file_where_are_kits()
        self.context = self.config['context']

    def __create_folder_and_config_file(self):
        # Create Config file if not exist

        self.create_config_file.create_folder()
        self.create_config_file.create_config_file()

    def __load_config_file_where_are_kits(self):
        """ Load Config ikctl """

        try:
            self.config = EnvYAML(self.path_config_file, strict=False)
        except FileNotFoundError:
            print("config file not found or not configured or env not defined")
            sys.exit()

        return self.config

    def load_config_file_kits(self):
        """ Load kits """

        kits = (self.config['contexts'][self.context]['path_kits'])
        try:
            return EnvYAML(kits + "/ikctl.yaml")
        except FileNotFoundError:
            print('config file not found or variable $VAR not defined')
            sys.exit()
        

    def load_config_file_servers(self):
        """ Load Hosts """

        servers = (self.config['contexts'][self.context]['path_servers'])
        try:
            return EnvYAML(servers + "/config.yaml")
        except FileNotFoundError:
            print('config file not found or variable $VAR not defined')
            sys.exit()
    

    def manage_context(self):
        """Change context"""

        # Convert to dict
        config_yaml = yaml.load(pathlib.Path.read_text(self.path_config_file),  Loader=SafeLoader)

        # Change context
        config_yaml['context'] = self.context

        # Convert to yaml
        config = yaml.dump(config_yaml, default_flow_style=False)

        # Save changes
        file = open(self.path_config_file, 'w', encoding="utf-8")
        file.writelines(config)
        file.close()


    def extract_config_servers(self, config, group=None):
        """ Extract values from config file """

        hosts = []

        for m in config["servers"]:
            if group == m["name"]:
                user     = m.get("user", "kub")
                port     = m.get("port", 22)
                password = m.get("password", "test")
                pkey     = m.get("pkey", None)
                for host in m["hosts"]:
                    hosts.append(host)
            elif group is None:
                user     = m.get("user", "kub")
                port     = m.get("port", 22)
                password = m.get("password", "test")
                pkey     = m.get("pkey", None)
                for host in m["hosts"]:
                    hosts.append(host)
            else:
                print("Host not found")
                sys.exit()
                
        return user, port, pkey, hosts, password
    
    def extrac_config_kits(self, config, name_kit):
        """ Extract values from config file """

        kits = []

        # Ruta donde se encuentran los kits
        path_kits = self.config['contexts'][self.context]['path_kits']

        # Recorremos los kits que hemos extraido de arriba
        for kit in config['kits']:

            # Buscamos la coincidencia con el kit que deseamos
            if name_kit == os.path.dirname(kit):

                # Generamos las rutas hasta donde están los kits
                # para poder subirlos a los servidores
                path_until_folder = os.path.dirname(path_kits + "/" + kit)
                object_with_path = EnvYAML(path_kits + "/" + kit)
                for k in object_with_path['kits']:
                    kits.append(path_until_folder + "/" + k)
                return kits
