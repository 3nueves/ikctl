import pathlib
import sys
import yaml
from yaml.loader import SafeLoader

from config import Config

class Context():
    """ Manage Contexts """
    
    def __init__(self):
        self.conf = Config()
        self.init_context()


    def init_context(self):
        """ load contexts """

        # Convert to dict
        self.config = yaml.load(pathlib.Path.read_text(self.conf.path_config_file),  Loader=SafeLoader)


    def check_context_exist(self, context):
        """Check if exist context"""

        # find if context exist
        for ctx in self.config['contexts']:
            if ctx == context:
                return True

        return False

    def change_context(self, context):
        """Change context"""

        # check if context exist
        if not self.check_context_exist(context):
            print('\n -- Context not exists --\n')
            sys.exit()

        # Change context
        self.config['context'] = context

        # Convert to yaml
        config_file = yaml.dump(self.config, default_flow_style=False)

        # Save changes
        file = open(self.conf.path_config_file, 'w', encoding="utf-8")
        file.writelines(config_file)
        file.close()

        print(f'\n\n-- Context "{context}" changed succefully --\n\n')
