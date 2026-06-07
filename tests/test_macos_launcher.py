from pathlib import Path
import subprocess


def test_macos_launcher_scripts_are_executable_and_valid():
    scripts = [
        Path("scripts/launch_macos.sh"),
        Path("scripts/build_macos_launcher.sh"),
    ]

    for script in scripts:
        assert script.is_file()
        assert script.stat().st_mode & 0o111
        subprocess.run(["bash", "-n", script], check=True)


def test_launcher_uses_local_only_production_server():
    body = Path("scripts/launch_macos.sh").read_text()

    assert '127.0.0.1:${PORT}' in body
    assert ".venv/bin/gunicorn" in body
    assert "run:app" in body
