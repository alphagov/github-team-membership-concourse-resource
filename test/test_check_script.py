import io
import json
import sys
from unittest.mock import patch

import pytest
import requests_mock

from src.lib import check_script


@patch('sys.stdin')
class TestCheckScript:

    input_json = json.dumps({
        'source': {
            'auth_user': 'Scarf Lady',
            'auth_token': 'shhhhh',
            'org': 'Flamingo',
            'team': 'John'
        },
        'version': {
            'hash': '12a14115c9b3f5027ed3b983f1b9315cdf48239d807f5c50294e95312c6ae0c1'
        }
    })

    @requests_mock.Mocker(kw='req_mocker')
    def test_returns_a_hash_of_the_current_membership(self, stdin_mock, **kwargs):
        stdin_mock.read.return_value = self.input_json
        kwargs['req_mocker'].get(
            'https://api.github.com/orgs/Flamingo/teams/John/members',
            json=[
                {'login': 'Sarah'},
                {'login': 'Duck'},
                {'login': 'Bread Man'},
            ]
        )

        captured_stdout = io.StringIO()
        sys.stdout = captured_stdout

        check_script.main()

        sys.stdout = sys.__stdout__

        assert captured_stdout.getvalue() == '[{"hash": "12a14115c9b3f5027ed3b983f1b9315cdf48239d807f5c50294e95312c6ae0c1"}]\n'

    def test_exits_if_invalid_source_input(self, stdin_mock):
        for source_key in ['auth_user', 'auth_token', 'org', 'team']:
            invalid_input_json = json.loads(self.input_json)
            invalid_input_json['source'][source_key] = None
            stdin_mock.read.return_value = json.dumps(invalid_input_json)

            captured_stderr = io.StringIO()
            sys.stderr = captured_stderr

            with pytest.raises(SystemExit) as e:
                check_script.main()

            sys.stderr = sys.__stderr__

            assert e.value.code == 1
            assert captured_stderr.getvalue() == f"[ERROR] {source_key} is not set\n"

    @requests_mock.Mocker(kw='req_mocker')
    def test_exits_if_bad_http_response(self, stdin_mock, **kwargs):
        stdin_mock.read.return_value = self.input_json
        kwargs['req_mocker'].get(
            'https://api.github.com/orgs/Flamingo/teams/John/members',
            status_code=400,
            reason="Oh no..."
        )

        captured_stderr = io.StringIO()
        sys.stderr = captured_stderr

        with pytest.raises(SystemExit) as e:
            check_script.main()

        sys.stderr = sys.__stderr__

        assert e.value.code == 1
        assert captured_stderr.getvalue() == "Fetching team membership for Flamingo/John\n" \
            "[ERROR] HTTPError when calling GitHub API: " \
            "400 Client Error: Oh no... for url: https://api.github.com/orgs/Flamingo/teams/John/members\n"
