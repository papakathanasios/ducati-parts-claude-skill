import subprocess


def _escape(text: str) -> str:
    """Escape backslashes and double quotes for AppleScript strings."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def send_macos_notification(
    title: str,
    message: str,
    subtitle: str = "",
    open_url: str | None = None,
) -> None:
    """Send a macOS notification using osascript / display notification."""
    escaped_message = _escape(message)
    escaped_title = _escape(title)
    escaped_subtitle = _escape(subtitle)

    script = f'display notification "{escaped_message}" with title "{escaped_title}"'
    if subtitle:
        script += f' subtitle "{escaped_subtitle}"'

    cmd = ["osascript", "-e", script]

    if open_url:
        escaped_url = _escape(open_url)
        open_script = f'open location "{escaped_url}"'
        cmd = ["osascript", "-e", script, "-e", open_script]

    subprocess.run(cmd, check=False, capture_output=True)
