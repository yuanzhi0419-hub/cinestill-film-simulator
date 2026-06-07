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


def test_launcher_icon_assets_are_bundled():
    icon_png = Path("assets/macos/camera-icon.png")
    icon_icns = Path("assets/macos/camera-icon.icns")
    launcher = Path("launcher/凤梨罐头 FILM LAB.app")
    build_script = Path("scripts/build_macos_launcher.sh").read_text()

    assert icon_png.stat().st_size > 100_000
    assert icon_icns.stat().st_size > 100_000
    assert (launcher / "Contents/Info.plist").is_file()
    assert (launcher / "Contents/Resources/applet.icns").is_file()
    assert "assets/macos/camera-icon.icns" in build_script
    assert "launcher/凤梨罐头 FILM LAB.app" in build_script
    assert "path to me" in build_script
