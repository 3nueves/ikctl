class Show:

    def __init__(self, kits, servers):
        self.kits = kits
        self.servers = servers

    def show_config(self, conf):            

        print()
        if "kit" in conf: 
            print("### KITS ###")
            print("------------")
            for value in self.kits['kits']:
                print("-- ", value.replace("/ikctl.yaml", ""))

        if "servers" in conf: 
            print("### SERVERS ###")
            print("---------------")
            for value in self.servers['servers']:
                print()
                for a in value.items():
                    print(a)

        print()
