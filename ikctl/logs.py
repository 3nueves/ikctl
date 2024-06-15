class Log:
    """ Class to show the stdout  """
    def __init__(self) -> None:
        pass

    def stdout(self, log, err, check):
        """ Method to get events """
        print()
        if check != 0:
            print(f'\x1b[31;1m{err}')
            print('\x1b[31;1mTask not completed')
            print("\x1b[0m")
        else:
            print(f'\033[1;32m{log}')
            print('Task completed')
            print("\x1b[0m")