""" Module to load cli """
import argparse

from .pipeline import Pipeline

def create_parser():
    """ CLI class """
    parser = argparse.ArgumentParser(description="tool for install software in remote servers", prog="ikctl")
    parser.add_argument("-l", "--list", choices=["kits", "servers", "context"], help="option to list kits, servers or context")
    parser.add_argument("-i", "--install", help="Select kit to use")
    parser.add_argument("-n", "--name", help="Name of the groups servers")
    parser.add_argument("-p", "--parameter", nargs = '*', help="Add parameters")
    parser.add_argument("-s", "--sudo", choices=["sudo"], help="exec from sudo")
    parser.add_argument("-c", "--context", help="Select context")
    return parser.parse_args()

Pipeline().init(create_parser())
