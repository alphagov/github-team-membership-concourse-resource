import io
import sys

from src.lib import out_script


class TestOutScript:
    def test_outputs_an_empty_version(self):
        captured_stdout = io.StringIO()
        sys.stdout = captured_stdout

        out_script.main()

        sys.stdout = sys.__stdout__

        assert captured_stdout.getvalue() == '{"version": {"hash": "none"}, "metadata": []}\n'
