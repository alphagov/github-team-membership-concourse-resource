import io
import json
import sys
from unittest.mock import patch

from freezegun import freeze_time
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
            'hash': 'someinputhash'
        }
    })

    @freeze_time("2020-03-08")
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

        assert captured_stdout.getvalue() == '[{"hash": "12a14115c9b3f5027ed3b983f1b9315cdf48239d807f5c50294e95312c6ae0c1-1583625600"}]\n'

    @freeze_time("1984-09-28")
    @requests_mock.Mocker(kw='req_mocker')
    def test_returns_a_hash_of_the_current_membership_when_no_version_supplied(self, stdin_mock, **kwargs):
        no_version_input = json.loads(self.input_json)
        del no_version_input['version']
        stdin_mock.read.return_value = json.dumps(no_version_input)
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

        assert captured_stdout.getvalue() == '[{"hash": "12a14115c9b3f5027ed3b983f1b9315cdf48239d807f5c50294e95312c6ae0c1-465177600"}]\n'

    @requests_mock.Mocker(kw='req_mocker')
    def test_returns_a_unique_version_for_previously_seen_team_membership(self, stdin_mock, **kwargs):
        stdin_mock.read.return_value = self.input_json
        kwargs['req_mocker'].get(
            'https://api.github.com/orgs/Flamingo/teams/John/members',
            [
                {'json': []},
                {'json': [
                    {'login': 'Sarah'},
                    {'login': 'Duck'},
                    {'login': 'Bread Man'},
                ]},
                {'json': []},

            ],
        )

        captured_stdout_1 = io.StringIO()
        sys.stdout = captured_stdout_1

        with freeze_time('1984-09-28 12:00:00'):
            check_script.main()

        version_1 = json.loads(captured_stdout_1.getvalue())[0]['hash']
        version_2_input = json.loads(self.input_json)
        version_2_input['version']['hash'] = version_1
        stdin_mock.read.return_value = json.dumps(version_2_input)

        captured_stdout_2 = io.StringIO()
        sys.stdout = captured_stdout_2

        with freeze_time('1984-09-28 12:05:00'):
            check_script.main()

        version_2 = json.loads(captured_stdout_2.getvalue())[0]['hash']
        version_3_input = json.loads(self.input_json)
        version_3_input['version']['hash'] = version_2
        stdin_mock.read.return_value = json.dumps(version_3_input)

        captured_stdout_3 = io.StringIO()
        sys.stdout = captured_stdout_3

        with freeze_time('1984-09-28 12:10:00'):
            check_script.main()

        version_3 = json.loads(captured_stdout_3.getvalue())[0]['hash']

        version_1_hash_and_timestamp = self.version_components(version_1)
        version_3_hash_and_timestamp = self.version_components(version_3)

        assert version_1_hash_and_timestamp['members_hash'] == version_3_hash_and_timestamp['members_hash']
        assert version_1_hash_and_timestamp['timestamp'] < version_3_hash_and_timestamp['timestamp']

    def version_components(self, version):
        components = version.split('-')
        return {'members_hash': components[0], 'timestamp': components[1]}

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
