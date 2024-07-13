""" Module to load cli """
import argparse

from .pipeline import Pipeline
from .config.config import __version__

def create_parser():
    """ CLI class """
    parser = argparse.ArgumentParser(description="tool for install software in remote and local machines", prog="ikctl")
    parser.version = __version__
    parser.add_argument("-l", "--list", choices=["kits", "servers", "context", "mode"], help="option to list kits, servers or context")
    parser.add_argument("-i", "--install", help="Select kit to use")
    parser.add_argument("-n", "--name", help="Name of the groups servers")
    parser.add_argument("-p", "--parameter", nargs = '*', help="Add parameters")
    parser.add_argument("-s", "--sudo", choices=["sudo"], help="exec from sudo")
    parser.add_argument("-c", "--context", help="Select context")
    parser.add_argument("-m", "--mode", choices=["local", "remote"], default="remote", help="Select mode")
    parser.add_argument("-v", "--version", action='version')
    return parser.parse_args()

if __name__ == "__main__":
    arg = create_parser()
    Pipeline(arg)
