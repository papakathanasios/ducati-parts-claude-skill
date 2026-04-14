import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PLIST_TEMPLATE = PROJECT_ROOT / "config" / "launchd" / "com.ducati-parts.watcher.plist"
PLIST_NAME = "com.ducati-parts.watcher"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"


def install_schedule(interval_hours: int = 4) -> str:
    plist_dest = LAUNCH_AGENTS_DIR / f"{PLIST_NAME}.plist"
    template_content = PLIST_TEMPLATE.read_text()
    venv_python = str(PROJECT_ROOT / ".venv" / "bin" / "python")
    content = (template_content
        .replace("__VENV_PYTHON__", venv_python)
        .replace("__PROJECT_ROOT__", str(PROJECT_ROOT))
        .replace("<integer>14400</integer>", f"<integer>{interval_hours * 3600}</integer>"))
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    plist_dest.write_text(content)
    subprocess.run(["launchctl", "unload", str(plist_dest)], check=False, capture_output=True)
    subprocess.run(["launchctl", "load", str(plist_dest)], check=True)
    return str(plist_dest)


def uninstall_schedule() -> None:
    plist_dest = LAUNCH_AGENTS_DIR / f"{PLIST_NAME}.plist"
    if plist_dest.exists():
        subprocess.run(["launchctl", "unload", str(plist_dest)], check=False, capture_output=True)
        plist_dest.unlink()


def is_installed() -> bool:
    plist_dest = LAUNCH_AGENTS_DIR / f"{PLIST_NAME}.plist"
    return plist_dest.exists()
