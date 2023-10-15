class Show:

    def __init__(self, kits, servers, context):
        self.kits = kits
        self.servers = servers
        self.contexts = context

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

        if "context" in conf:
            print(" ### Contexts ###")
            print(" ----------------")
            for ctx in self.contexts['contexts']:
                print(f' -- {ctx}')
            print(f"\n - Context use: {self.contexts['context']}")
        print()
