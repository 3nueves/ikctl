class Show:
    """ Class to show the app config """

    def __init__(self, kits, servers, context, mode):
        self.kits = kits
        self.servers = servers
        self.contexts = context
        self.mode = mode

    def show_config(self, conf):
        """ show config of the kits, servers and context """

        print(f"\n### {conf.upper()} ###\n")

        if "kit" in conf:
            for value in self.kits['kits']:
                print("-- ", value.replace("/ikctl.yaml", ""))

        elif "context" in conf:
            for ctx in self.contexts['contexts']:
                print(f' -- {ctx}')
            print(f"\n - Mode: {self.mode}")
            print(f" - Context: {self.contexts['context']}")

        elif "mode" in conf:
            print(f" - Context: {self.contexts['context']}")

        elif "servers" in conf and self.mode != "local":
            for value in self.servers['servers']:
                print("")
                for key, value in value.items():
                    print(f"{key}: {value}")
        else:
            print(f"\nYou are in {self.mode} mode")

        print()
