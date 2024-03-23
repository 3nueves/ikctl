import pathlib
import yaml
from os import path

class CreateFolderAndConfigFile():
    """
    Creating Folder and Config File 
    """

    config = { 
        'contexts': {
            'local': {
                'path_kits':'/', 
                'path_servers':'/'}, 
           'remote': {
                'path_kits':'/', 
                'path_servers':'/'}
        },
        'context' : 'local'
    }

    def __init__(self):
        self.home = pathlib.Path.home()
        self.path_config_file = self.home.joinpath('.ikctl')
        self.yaml_data = yaml.dump(self.config, default_flow_style=False)


    def create_folder(self):
        """Create Folder if not exist"""

        if not path.exists(self.path_config_file):
            pathlib.Path.mkdir(self.path_config_file)
        else:
            return True


    def create_config_file(self):
        """Create config file if not exist"""

        if not path.exists(str(self.path_config_file) + "/config"):
            with open(str(self.path_config_file) + "/config", "a+", encoding="utf-8") as file:
                file.seek(0)
                try:
                    file.writelines(self.yaml_data)
                    return True
                except:
                    print("Error Creating File")
        else:
            return True
