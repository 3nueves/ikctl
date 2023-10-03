import os
from config import Config

class Show:

    ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__)))

    data = Config()

    def __init__(self) -> None:
        pass

    def load_config(self, conf):
        config = self.data.load_config(self.ROOT_DIR+'/'+"ikctl.yaml")
        config = self.data.load_config(config["kits"]+'ikctl.yaml')
        if "config.yaml" in conf:
            config = self.data.load_config(self.ROOT_DIR+'/'+"ikctl.yaml")
            config = self.data.load_config(config["kits"]+"config.yaml")
        return config
    
    def load_ikctl(self, file):
        config = self.data.load_config(self.ROOT_DIR + '/' + file)
        return config

    def show_config(self, conf):            
        config = self.load_config(conf)
        print()
        if "kits" in config: 
            print("### KITS ###")
            print("------------")
        if "servers" in config: 
            print("### SERVERS ###")
            print("---------------")
        self.print_config(config)
        print()


    def print_config(self, conf):
        if "kits" in conf:
            for value in conf.values():
                for scripts in value:
                    print("-- ", scripts.replace("/ikctl.yaml", ""))
        if "servers" in conf:
            for value in conf.values():
                for a in value:
                    print()
                    for c in a.items():
                        print(c)


    def parse_config(self, data):
        config = ' '.join(data)
        return config
