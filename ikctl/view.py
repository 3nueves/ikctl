class Show:
    """ Class to show the app config """

    def __init__(self, kits, servers, context):
        self.kits = kits
        self.servers = servers
        self.contexts = context

    def show_config(self, conf):
        """ show config of the kits, servers and context """
        if "kit" in conf:
            print("\n### KITS ###")
            print("------------")
            for value in self.kits['kits']:
                print("-- ", value.replace("/ikctl.yaml", ""))

        if "servers" in conf:
            print("\n### SERVERS ###")
            print("---------------")
            for value in self.servers['servers']:
                print("")
                for key, value in value.items():
                    print(f"{key}: {value}")

        if "context" in conf:
            print("\n### Contexts ###")
            print(" ----------------")
            for ctx in self.contexts['contexts']:
                print(f' -- {ctx}')
            print(f"\n - Context use: {self.contexts['context']}")
        print()
