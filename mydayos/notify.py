"""macOS notification driver — the preemption channel's first delivery device.

A ring-3 *output* device (the terminal bell, upgraded): ring 0 decides WHEN
to preempt (eventually governed by the context-switch threshold (K1) and
masking windows (K2); unconditional in this skeleton), this driver only
delivers. Zero-dependency via `osascript`; the subprocess runner is injected
so tests never touch the real notification center, and so richer drivers
(terminal-notifier / alerter, which support buttons and replies) can swap in
without the dispatcher noticing.

Try it: `just notify-test` (or `python -m mydayos.notify "message"`).
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from typing import Protocol

__all__ = ["MacNotifier", "Notifier"]


class Notifier(Protocol):
    """What the dispatcher needs from a notification device."""

    def notify(self, title: str, message: str, subtitle: str | None = None) -> None:
        """Deliver one notification to the human."""


class MacNotifier:
    """Banner notifications via osascript (macOS Notification Center)."""

    def __init__(
        self, runner: Callable[..., object] = subprocess.run, *, sound: bool = True
    ) -> None:
        self._runner = runner
        self._sound = sound

    def notify(self, title: str, message: str, subtitle: str | None = None) -> None:
        # json.dumps produces a double-quoted, escaped AppleScript string.
        script = f"display notification {json.dumps(message)}"
        script += f" with title {json.dumps(title)}"
        if subtitle:
            script += f" subtitle {json.dumps(subtitle)}"
        if self._sound:
            script += ' sound name "Glass"'
        self._runner(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
        )


def main() -> int:
    message = " ".join(sys.argv[1:]) or "The deli is open — ticket rail online."
    MacNotifier().notify("my-day-os", message, subtitle="preemption channel test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
