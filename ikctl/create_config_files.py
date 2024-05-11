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
                'path_kits':'$HOME/kits', 
                'path_servers':'$HOME/kits', 
                'path_secrets': ''
            },
           'remote': {
                'path_kits':'', 
                'path_servers':'',
                'path_secrets': ''
            }
        },
        'context' : 'local'
    }

    config_servers = {
        'servers': [
            {
            'name':'mariadb',
            'user': 'root',
            'hosts': ['192.168.1.55', '10.0.0.234'],
            'port':'3306',
            'password':'$PASSWORD',
            'pkey': "/home/dml/.ssh/id_rsa_kubernetes-unelink"
            }
        ]
    }

    config_kits = {
        'kits': {
            'create-users/ikctl.yaml',
            'install-mariadb/ikctl.yaml'
        }
    }

    answer = 'yes'
    answer_kits = 'yes'

    def __init__(self):
        self.home = pathlib.Path.home()
        self.path_config_file = self.home.joinpath('.ikctl')
        self.path_config_kits_servers = self.home.joinpath('kits')
        self.yaml_data = yaml.dump(self.config, default_flow_style=False)
        self.yaml_config_servers = yaml.dump(self.config_servers, default_flow_style=False)
        self.yaml_config_kits = yaml.dump(self.config_kits, default_flow_style=False)


    def create_folder(self):
        """Create Folder if not exist"""

        if not path.exists(self.path_config_file):
            self.answer = input("\nDo you want to create configuration files automatically? [yes, no]\n")
            if self.answer == 'yes':
                pathlib.Path.mkdir(self.path_config_file)

        if not path.exists(self.path_config_kits_servers):
            self.answer_kits = input("\nDo you want to create configuration of servers and kits automatically? [yes, no]\n")
            if self.answer_kits == 'yes':
                pathlib.Path.mkdir(self.path_config_kits_servers)
        else:
            return True

    def create_config_file(self):
        """Create config file if not exist"""

        if not path.exists(str(self.path_config_kits_servers) + "/ikctl.yaml") and self.answer_kits == 'yes':
            with open(str(self.path_config_kits_servers) + "/ikctl.yaml", "a+", encoding="utf-8") as file:
                file.seek(0)
                try:
                    file.writelines(self.yaml_config_kits)
                except ValueError:
                    print("Error Creating File")


        if not path.exists(str(self.path_config_kits_servers) + "/config.yaml") and self.answer_kits == 'yes':
            with open(str(self.path_config_kits_servers) + "/config.yaml", "a+", encoding="utf-8") as file:
                file.seek(0)
                try:
                    file.writelines(self.yaml_config_servers)
                except ValueError:
                    print("Error Creating File")

        if not path.exists(str(self.path_config_file) + "/config") and self.answer == 'yes':
            # print(self.answer)
            with open(str(self.path_config_file) + "/config", "a+", encoding="utf-8") as file:
                file.seek(0)
                try:
                    file.writelines(self.yaml_data)
                    return True
                except ValueError:
                    print("Error Creating File")
        else:
            return True
