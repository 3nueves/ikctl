# 1.- Cargar archivo desde la $HOME/.ikctl
# 2.- Comprobar que existe el directorio $HOME/.ikctl
# 3.- Si no existe avisar que no existe
# 5.- Si existe el fichero cargarlo y retornarlo

import pathlib
from envyaml import EnvYAML

class Config():
    """Load path where are kits"""

    def __init__(self):
        self.home = pathlib.Path.home()
        self.path_config_file = self.home.joinpath('.ikctl/config')
        self.__load_config_file_path_where_are_kits()

    def __load_config_file_path_where_are_kits(self):
        """ Load Config ikctl """
        try:
            config = EnvYAML(self.path_config_file)
            return config
        except FileNotFoundError:
            print('This file doesn\'t exist')
    
    def __load_config_file_kits(self):
        pass

    def __load_config_file_servers(self):
        pass