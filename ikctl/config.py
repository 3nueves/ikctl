import os
import yaml
from yaml.loader import SafeLoader
# from schema import Regex, Schema, SchemaError, Or, Optional


class Config:

    hosts = []
    ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__)))

    def __init__(self)-> None:
        pass

    # Load config
    def load_config(self, file):

        with open(file, "r") as stream:
            try:
                data = yaml.load(stream, Loader=SafeLoader)
            except yaml.YAMLError as exc:
                print(exc)

        return data

    def extract_config_servers(self, config, group=None):

        for m in config["servers"]:
            if group == m["name"]:
                self.user     = m.get("user", "kub")
                self.port     = m.get("port", 22)
                self.password = m.get("password", "test")
                if self.password.startswith('$'):
                    self.password = os.getenv(self.password[1:])
                self.pkey     = m.get("pkey", None)
                for host in m["hosts"]:
                    self.hosts.append(host)
            elif group == None:
                self.user     = m.get("user", "kub")
                self.port     = m.get("port", 22)
                self.password = m.get("password", "test")
                if self.password.startswith('$'):
                    self.password = os.getenv(self.password[1:])
                self.pkey     = m.get("pkey", None)
                for host in m["hosts"]:
                    self.hosts.append(host)
        return self.user, self.port, self.pkey, self.hosts, self.password
