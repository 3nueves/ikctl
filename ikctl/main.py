#!/usr/bin/env python
import argparse
from pipeline import Pipeline

def create_parser():
    parser = argparse.ArgumentParser(description="tool for install software in remote servers", prog="ikctl")

    parser.add_argument("-l", "--list", choices=["kit", "servers", "context"], help="List of all kit")
    parser.add_argument("-i", "--install", help="Install all kits or kit selected")
    parser.add_argument("-n", "--name", help="Name of the groups servers")
    parser.add_argument("-p", "--parameter", help="Add parameters")
    parser.add_argument("-s", "--sudo", choices=["sudo"], help="exec from sudo")
    parser.add_argument("-c", "--context", help="Select context")
    
    args = parser.parse_args()
    
    return args

options = create_parser()

pipeline = Pipeline()

pipeline.init(options)
