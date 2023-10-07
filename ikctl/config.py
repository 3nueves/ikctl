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

class Config():
    """
    Load path where are kits

    var:
        change_context => Value to change context
    """

    def __init__(self, change_context=None):
        self.config = ""
        self.hosts = []
        self.change_context = change_context
        self.home = pathlib.Path.home()
        self.path_config_file = self.home.joinpath('.ikctl/config')
        self.__load_config_file_where_are_kits()
        self.context = self.config['context']


    def __load_config_file_where_are_kits(self):
        """ Load Config ikctl """

        try:
            self.config = EnvYAML(self.path_config_file, strict=False)
        except FileNotFoundError:
            print(f'config file not found or variable $VAR not defined')

        return self.config

    def load_config_file_kits(self):
        """ Load kits """

        kits = (self.config['contexts'][self.context]['path_kits'])
        try:
            return EnvYAML(kits + "/ikctl.yaml")
        except:
            print(f'config file not found or variable $VAR not defined')
            sys.exit()
        

    def load_config_file_servers(self):
        """ Load Hosts """

        servers = (self.config['contexts'][self.context]['path_servers'])
        try:
            return EnvYAML(servers + "/config.yaml")
        except:
            print(f'config file not found or variable $VAR not defined')
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

        for m in config["servers"]:
            if group == m["name"]:
                self.user     = m.get("user", "kub")
                self.port     = m.get("port", 22)
                self.password = m.get("password", "test")
                # if self.password.startswith('$'):
                #     self.password = os.getenv(self.password[1:])
                self.pkey     = m.get("pkey", None)
                for host in m["hosts"]:
                    self.hosts.append(host)
            elif group == None:
                self.user     = m.get("user", "kub")
                self.port     = m.get("port", 22)
                self.password = m.get("password", "test")
                # if self.password.startswith('$'):
                #     self.password = os.getenv(self.password[1:])
                self.pkey     = m.get("pkey", None)
                for host in m["hosts"]:
                    self.hosts.append(host)
        return self.user, self.port, self.pkey, self.hosts, self.password
    
    def extrac_config_kits(self, config, name_kit):

        for kit in config['kits']:
            if name_kit == os.path.dirname(kit):
                return kit
