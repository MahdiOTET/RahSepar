import subprocess
import sys


def test_cli_help_lists_completed_commands() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "app", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for command in (
        "tickets",
        "book",
        "cancel",
        "import-buses",
        "create-trip",
        "hourly-report",
        "monthly-bus-report",
        "busiest-drivers",
    ):
        assert command in result.stdout
