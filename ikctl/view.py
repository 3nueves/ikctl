class Show:
    """ Class to show the app config """

    def __init__(self, kits, path_kits, servers, path_servers, context, mode):
        self.kits = kits
        self.path_kits = path_kits
        self.servers = servers
        self.path_servers = path_servers
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
            print(f" - Path Kits: {self.path_kits}")
            print(f" - Path Servers: {self.path_servers}")

        elif "mode" in conf:
            print(f" - Context: {self.contexts['context']}")

        elif "servers" in conf and self.mode != "local":
            for value in self.servers['servers']:
                print("")
                for key, value in value.items():
                    if key == "password":
                        value = "*****"
                    print(f"{key}: {value}")
        else:
            print(f"\nYou are in {self.mode} mode")

        print()
