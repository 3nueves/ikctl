from config import Config

class Show:

    data = Config()

    def __init__(self):
        self.kits = self.data.load_config_file_kits()
        self.servers = self.data.load_config_file_servers()

    def show_config(self, conf):            

        print()
        if "kit" in conf: 
            print("### KITS ###")
            print("------------")
            self.print_config(self.kits)

        if "servers" in conf: 
            print("### SERVERS ###")
            print("---------------")
            self.print_config(self.servers)

        print()


    def print_config(self, conf):

        if "kits" in conf:
            for value in conf['kits']:
                print("-- ", value.replace("/ikctl.yaml", ""))
        if "servers" in conf:
            for value in conf['servers']:
                print()
                for a in value.items():
                    print(a)
