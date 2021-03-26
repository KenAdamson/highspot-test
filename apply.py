#!/usr/bin/env python3

import argparse
import json

from changes import MixtapeChanges
from mixtapes import NaiveMixtape, OptimizedMixtape


def get_args():
    parser = argparse.ArgumentParser('Apply some changes')
    parser.add_argument('-i', '--input', dest='input_file', required=True, help='Input filename')
    parser.add_argument('-o', '--changes', dest='changes_file', required=True, help='Changes filename')
    return parser.parse_args()


def load_files(arguments):
    in_file = json.load(open(arguments.input_file))
    change_file = json.load(open(arguments.changes_file))
    return in_file, change_file


if __name__ == '__main__':
    args = get_args()
    input_file, changes_file = load_files(args)

    mixtape = NaiveMixtape(input_file)
    mixtape_changes = MixtapeChanges(changes_file)

    mixtape.apply(mixtape_changes)
    output = json.dumps(mixtape.mixtape, indent=4)
    print(output)
