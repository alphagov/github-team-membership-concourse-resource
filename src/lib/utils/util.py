#!/usr/bin/env python

import hashlib
import sys

import requests
from requests import HTTPError


def eprint(message):
    print(message, file=sys.stderr)


def validate_source(source):
    if source.get("auth_user") is None:
        eprint("[ERROR] auth_user is not set")
        exit(1)
    if source.get("auth_token") is None:
        eprint("[ERROR] auth_token is not set")
        exit(1)
    if source.get("org") is None:
        eprint("[ERROR] org is not set")
        exit(1)
    if source.get("team") is None:
        eprint("[ERROR] team is not set")
        exit(1)


def call_github_api(source):
    eprint(f"Fetching team membership for {source['org']}/{source['team']}")
    response = requests.get(
        f"https://api.github.com/orgs/{source['org']}/teams/{source['team']}/members",
        auth=(source["auth_user"], source["auth_token"]),
        headers={"Accept": "application/vnd.github.v3+json"},
    )

    try:
        response.raise_for_status()
        eprint("Success!")
    except HTTPError as e:
        eprint(f"[ERROR] HTTPError when calling GitHub API: {e}")
        exit(1)

    return response


def get_hash_of_members(response):
    members = sorted([member["login"] for member in response.json()])
    eprint("Team members:")
    for member in members:
        eprint(f"    {member}")
    return hashlib.sha256(''.join(members).encode('utf-8')).hexdigest()
