# Concourse GitHub Team Membership Resource

[Concourse][concourse] resource for checking changes to [GitHub][gh] team membership.

This is useful for monitoring the membership of a team. The intended use case for this
is to feed into a slack alert to inform us when a member has been added to a team.

## Source Configuration

* `auth_user`: *Required*<br/>The username to authenticate with GitHub.
* `auth_token`: *Required*<br/>The personal access token for the user named above.
* `org`: *Required*<br/>The name of the organisation the team belongs to.
* `team`: *Required*<br/>The name of the GitHub team.

## Behaviour

### `check`:

Fetches the current list of team members, calculates a hash of their names, and reports it.

### `in`:

Fetches the current list of team members and writes their login names to file - `./team-members`

Will throw an error if the team membership has changed from the version requested. This could happen
if members have been added/removed between the check and the get. Re-running should be sufficient.

### `out`: Not implemented

<hr>

## Example Configuration

### Resource Type

```
resource_types:
  - name: github-team-membership
    type: registry-image
    source:
      repository: 753415395406.dkr.ecr.eu-west-2.amazonaws.com/platform-deployer-github-team-membership-concourse-resource
      tag: latest
```

### Resource

```
resources:
  - name: verify-concourse-admins
    icon: git
    type: github-team-membership
    source:
      auth_user: wynndow
      auth_token: <PERSONAL_ACCESS_TOKEN>
      org: alphagov
      team: verify-tech-team-concourse-admins
```

### Plan

```
jobs:
  - name: do-thing
    plan:
      - get: verify-concourse-admins
        trigger: true
      - task: do-the-thing
        image: some-base-image
        config:
          platform: linux
          inputs:
            - name: verify-concourse-admins
          run:
            path: bash
            args:
              - -c
              - cat verify-concourse-admins/team-members
```

## Running the tests

Install required dependencies with:

```
pip install -r requirements-dev.txt
```

Then from the root of the repo run:

```
python -m pytest
```

[gh]: https://github.com
[concourse]: https://concourse-ci.org
