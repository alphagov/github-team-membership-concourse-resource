#!/usr/bin/env python

import json
import sys
import time

from .utils import call_github_api, get_hash_of_members, members_hash_from_version, validate_source


def main():
    input_json = json.loads(sys.stdin.read())
    source = input_json.get("source")
    version = input_json.get("version")

    validate_source(source)
    response = call_github_api(source)
    members_hash = get_hash_of_members(response)

    if not version or members_hash != members_hash_from_version(version):
        print(f'[{{"hash": "{suffix_timestamp(members_hash)}"}}]')
    else:
        print(f'[{{"hash": "{version.get("hash")}"}}]')


def suffix_timestamp(hash):
    return f"{hash}-{int(time.time())}"



if __name__ == '__main__':
    main()
