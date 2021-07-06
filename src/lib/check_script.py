#!/usr/bin/env python

import json
import sys

from .utils import call_github_api, get_hash_of_members, validate_source


def main():
    input_json = json.loads(sys.stdin.read())
    source = input_json.get("source")

    validate_source(source)
    response = call_github_api(source)

    print(f'[{{"hash": "{get_hash_of_members(response)}"}}]')


if __name__ == '__main__':
    main()
