""" Module to load cli """
import argparse

from ikctl.pipeline import Pipeline

def create_parser():
    """ CLI class """
    parser = argparse.ArgumentParser(description="tool for install software in remote servers", prog="ikctl")
    parser.version = Pipeline().version
    parser.add_argument("-l", "--list", choices=["kits", "servers", "context"], help="option to list kits, servers or context")
    parser.add_argument("-i", "--install", help="Select kit to use")
    parser.add_argument("-n", "--name", help="Name of the groups servers")
    parser.add_argument("-p", "--parameter", nargs = '*', help="Add parameters")
    parser.add_argument("-s", "--sudo", choices=["sudo"], help="exec from sudo")
    parser.add_argument("-c", "--context", help="Select context")
    parser.add_argument("-v", "--version", action='version')
    return parser.parse_args()

Pipeline().init(create_parser())
