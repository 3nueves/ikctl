class Log:
    """ Class to show the stdout  """
    def __init__(self) -> None:
        pass

    def stdout(self, logger, log, err, check, level):
        """ Method to get events """
        print()
        if check != 0:
            print(f'\x1b[31;1mTask not completed::NOK')
            print("\x1b[0m")
        else:
            print(f'\033[1;32mTask completed:OK')
            print("\x1b[0m")