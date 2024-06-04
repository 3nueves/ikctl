class Show:
    """ Class to show the app config """

    def __init__(self, kits, servers, context, mode):
        self.kits = kits
        self.servers = servers
        self.contexts = context
        self.mode = mode

    def show_config(self, conf):
        """ show config of the kits, servers and context """
        if "kit" in conf:
            print("\n### KITS ###")
            print("------------")
            for value in self.kits['kits']:
                print("-- ", value.replace("/ikctl.yaml", ""))

        if "servers" in conf and self.mode != "local":
            print("\n### SERVERS ###")
            print("---------------")
            for value in self.servers['servers']:
                print("")
                for key, value in value.items():
                    print(f"{key}: {value}")
        else:
            print(f"\nYou are in {self.mode} mode")

        if "context" in conf:
            print("\n### Contexts ###")
            print(" ----------------")
            for ctx in self.contexts['contexts']:
                print(f' -- {ctx}')
            print(f"\n - Context use: {self.contexts['context']}")
        print()
