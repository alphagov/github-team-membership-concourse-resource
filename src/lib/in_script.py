#!/usr/bin/env python

import json
import sys

from .utils import call_github_api, eprint, get_hash_of_members, validate_source


def main():
    input_json = json.loads(sys.stdin.read())
    source = input_json.get("source")
    requested_version = input_json.get("version").get('hash')
    destination_dir = sys.argv[1]

    validate_source(source)
    response = call_github_api(source)

    current_version = get_hash_of_members(response)

    if requested_version != current_version:
        eprint(
            f"[ERROR] Requested version ({requested_version[0:8]}) does not match current version ({current_version[0:8]})."
            " The team membership was probably updated between the check and the get."
        )
        exit(1)

    with open(f"{destination_dir}/team-members", "w") as f:
        for member_login in sorted([member["login"] for member in response.json()]):
            f.write(f"{member_login}\n")

    output = {
        "version": {"hash": current_version},
        "metadata": [
            {"name": "organisation", "value": source['org']},
            {"name": "team", "value": source['team']},
        ]
    }
    print(json.dumps(output))


if __name__ == '__main__':
    main()
