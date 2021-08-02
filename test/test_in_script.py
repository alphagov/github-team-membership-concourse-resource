import io
import json
import sys
from unittest.mock import patch

from freezegun import freeze_time
import pytest
import requests_mock

from src.lib import in_script


@pytest.fixture(scope="session")
def temp_dir(tmpdir_factory):
    dirname = tmpdir_factory.mktemp('fake_concourse_dir')
    return dirname


@patch('sys.stdin')
class TestInScript:

    input_json = json.dumps({
        'source': {
            'auth_user': 'Scarf Lady',
            'auth_token': 'shhhhh',
            'org': 'Flamingo',
            'team': 'John'
        },
        'version': {
            'hash': '12a14115c9b3f5027ed3b983f1b9315cdf48239d807f5c50294e95312c6ae0c1-1583625600'
        }
    })

    @freeze_time("2020-03-08")
    @requests_mock.Mocker(kw='req_mocker')
    def test_returns_the_version_and_writes_members_to_file(self, stdin_mock, temp_dir, **kwargs):
        with patch.object(sys, 'argv', ['_', temp_dir]):
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

            in_script.main()

            sys.stdout = sys.__stdout__

            assert captured_stdout.getvalue() == '{' \
                '"version": {"hash": "12a14115c9b3f5027ed3b983f1b9315cdf48239d807f5c50294e95312c6ae0c1-1583625600"}, ' \
                '"metadata": [' \
                    '{"name": "organisation", "value": "Flamingo"}, ' \
                    '{"name": "team", "value": "John"}' \
                ']' \
            '}\n'

            with open(f"{temp_dir}/team-members", "r") as f:
                members = [line.strip() for line in f.readlines()]
                assert members == ['Bread Man', 'Duck', 'Sarah']

    def test_exits_if_invalid_source_input(self, stdin_mock, temp_dir):
        with patch.object(sys, 'argv', ['_', temp_dir]):
            for source_key in ['auth_user', 'auth_token', 'org', 'team']:
                invalid_input_json = json.loads(self.input_json)
                invalid_input_json['source'][source_key] = None
                stdin_mock.read.return_value = json.dumps(invalid_input_json)

                captured_stderr = io.StringIO()
                sys.stderr = captured_stderr

                with pytest.raises(SystemExit) as e:
                    in_script.main()

                sys.stderr = sys.__stderr__

                assert e.value.code == 1
                assert captured_stderr.getvalue() == f"[ERROR] {source_key} is not set\n"

    @requests_mock.Mocker(kw='req_mocker')
    def test_exits_if_bad_http_response(self, stdin_mock, temp_dir, **kwargs):
        with patch.object(sys, 'argv', ['_', temp_dir]):
            stdin_mock.read.return_value = self.input_json
            kwargs['req_mocker'].get(
                'https://api.github.com/orgs/Flamingo/teams/John/members',
                status_code=400,
                reason="Oh no..."
            )

            captured_stderr = io.StringIO()
            sys.stderr = captured_stderr

            with pytest.raises(SystemExit) as e:
                in_script.main()

            sys.stderr = sys.__stderr__

            assert e.value.code == 1
            assert captured_stderr.getvalue() == "Fetching team membership for Flamingo/John\n" \
                "[ERROR] HTTPError when calling GitHub API: " \
                "400 Client Error: Oh no... for url: https://api.github.com/orgs/Flamingo/teams/John/members\n"

    @requests_mock.Mocker(kw='req_mocker')
    def test_exits_if_requested_version_does_not_equal_current_version(self, stdin_mock, temp_dir, **kwargs):
        with patch.object(sys, 'argv', ['_', temp_dir]):
            stdin_mock.read.return_value = self.input_json
            kwargs['req_mocker'].get(
                'https://api.github.com/orgs/Flamingo/teams/John/members',
                json=[
                    {'login': 'Moon'},
                    {'login': 'Donkey'},
                    {'login': 'Umbrella'},
                ]
            )

            captured_stderr = io.StringIO()
            sys.stderr = captured_stderr

            with pytest.raises(SystemExit) as e:
                in_script.main()

            sys.stderr = sys.__stderr__

            assert e.value.code == 1
            assert "[ERROR] Requested version (12a14115) does not match current version (985f3e1f). " \
                   "The team membership was probably updated between the check and the get." in captured_stderr.getvalue()








