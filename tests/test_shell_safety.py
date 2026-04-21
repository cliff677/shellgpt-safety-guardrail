from unittest.mock import Mock, patch

from sgpt.llm_functions.common.execute_shell import Function
from sgpt.shell_safety import analyze_shell_command

from .utils import app, cmd_args, mock_comp, runner


def test_analyze_shell_command_detects_high_risk():
    report = analyze_shell_command("rm -rf ~/tmp")

    assert report.has_issues
    assert report.is_high_risk
    assert any(issue.title == "Destructive deletion" for issue in report.issues)


def test_analyze_shell_command_detects_medium_risk():
    report = analyze_shell_command("chmod -R 755 ./project")

    assert report.has_issues
    assert not report.is_high_risk
    assert any(issue.title == "Recursive permission change" for issue in report.issues)


@patch("sgpt.app.run_command")
@patch("sgpt.handlers.handler.completion")
def test_shell_high_risk_requires_confirmation(completion, run_command):
    completion.return_value = mock_comp("rm -rf ~/tmp")

    args = {"prompt": "delete temp folder", "--shell": True}
    inputs = "__sgpt__eof__\ne\nn\na\n"
    result = runner.invoke(app, cmd_args(**args), input=inputs)

    run_command.assert_not_called()
    assert result.exit_code == 0
    assert "Shell safety check: HIGH RISK command detected." in result.output
    assert "Execute this command anyway?" in result.output


@patch("sgpt.app.run_command")
@patch("sgpt.handlers.handler.completion")
def test_shell_safety_can_be_disabled(completion, run_command):
    completion.return_value = mock_comp("rm -rf ~/tmp")

    args = {
        "prompt": "delete temp folder",
        "--shell": True,
        "--no-shell-safety": True,
    }
    inputs = "__sgpt__eof__\ne\n"
    result = runner.invoke(app, cmd_args(**args), input=inputs)

    run_command.assert_called_once_with("rm -rf ~/tmp")
    assert result.exit_code == 0
    assert "Shell safety check" not in result.output


@patch("sgpt.handlers.repl_handler.run_command")
@patch("sgpt.handlers.handler.completion")
def test_shell_repl_high_risk_requires_confirmation(completion, run_command):
    completion.return_value = mock_comp("rm -rf ~/tmp")

    args = {"--repl": "temp", "--shell": True}
    inputs = "__sgpt__eof__\ndelete temp folder\ne\nn\nexit()\n"
    result = runner.invoke(app, cmd_args(**args), input=inputs)

    run_command.assert_not_called()
    assert result.exit_code == 0
    assert "Shell safety check: HIGH RISK command detected." in result.output


@patch("sgpt.llm_functions.common.execute_shell.subprocess.Popen")
def test_execute_shell_function_blocks_high_risk_command(popen):
    result = Function.execute("rm -rf ~/tmp")

    popen.assert_not_called()
    assert result.startswith("Blocked high-risk shell command by ShellGPT safety check.")


@patch("sgpt.llm_functions.common.execute_shell.subprocess.Popen")
def test_execute_shell_function_allows_safe_command(popen):
    process = Mock()
    process.communicate.return_value = (b"hello\n", None)
    process.returncode = 0
    popen.return_value = process

    result = Function.execute("echo hello")

    popen.assert_called_once()
    assert result == "Exit code: 0, Output:\nhello\n"
