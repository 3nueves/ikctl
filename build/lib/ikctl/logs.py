import logging
class Log:
    """ Class to show the stdout  """
    def __init__(self) -> None:
        pass

    def stdout(self, logs=None, errors=None, check=None):
        """ Method to get events """
        print()
        if check != 0:
            if errors is None:
                print('\x1b[31;1mEnd task with errors')
            else:
                print(f'\x1b[31;1m{errors}')
                print('\x1b[31;1mEnd task with errors')
        else:
            if logs is None:
                print('\033[1;32mEnd task succefully')
            else:
                print(f'\033[1;32m{logs}')
                print('\033[1;32mEnd task succefully')
        print("\x1b[0m")