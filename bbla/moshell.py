from __future__ import annotations

import re
import time
from pathlib import Path

import pexpect

from .utils import strip_ansi


class MoShellSession:
    """
    Thin wrapper over pexpect to talk to MoShell reliably.

    Key behavior:
    - Wait initial base prompt: "<ip>>"
    - Login via: lt all -> username -> password
    - Commands: run(cmd) waits for echo of cmd, then waits for prompt, returns output between.
    """

    def __init__(self, moshell_path: Path, ip: str) -> None:
        self.moshell_path = moshell_path
        self.ip = ip
        self.child: pexpect.spawn | None = None

        ANSI = r"(?:\x1b\[[0-9;]*m)*"
        self.base_prompt = re.compile(ANSI + re.escape(ip) + ANSI + r">\s*$")
        self.any_prompt = re.compile(ANSI + r"[^\s]{1,80}" + ANSI + r">\s*$")

    def open(self) -> None:
        self.child = pexpect.spawn(
            "bash",
            [str(self.moshell_path), self.ip],
            encoding="utf-8",
            timeout=180,
            cwd=str(Path.home()),
        )
        # Ensure we land at base prompt
        self.child.sendline("")
        self.child.expect(self.base_prompt, timeout=180)

    def close(self) -> None:
        if not self.child:
            return
        try:
            self.child.sendline("exit")
        except Exception:
            pass
        try:
            self.child.close(force=True)
        except Exception:
            pass
        self.child = None

    def _drain_prompts(self, max_drains: int = 5) -> None:
        """
        MoShell sometimes prints extra prompts; drain queued prompts so next expect
        won't match an old prompt immediately.
        """
        assert self.child
        for _ in range(max_drains):
            try:
                self.child.expect(self.any_prompt, timeout=0.2)
            except pexpect.TIMEOUT:
                break

    def run(self, cmd: str, timeout: int) -> tuple[str, float]:
        """
        Send cmd, wait for echo, then wait for prompt. Return (output, duration_s).
        """
        assert self.child
        self._drain_prompts()
        t0 = time.time()

        self.child.sendline(cmd)
        echo_re = re.compile(rf"(?m)^\s*{re.escape(cmd)}\s*$")
        self.child.expect(echo_re, timeout=5)

        self.child.expect(self.any_prompt, timeout=timeout)
        return self.child.before, (time.time() - t0)

    def login_with_passwords(self, username: str, passwords: list[str]) -> str:
        """
        Try passwords in order. Returns node prompt (e.g. "BB52>") on success.

        On wrong password, MoShell returns to base prompt; we restart lt all.
        """
        assert self.child
        if not passwords:
            raise RuntimeError("No baseband passwords provided (secrets.json: baseband.passwords)")

        self.child.sendline("lt all")
        self.child.expect("Please enter Username:", timeout=180)
        self.child.sendline(username)

        for pw in passwords:
            self.child.expect("Node Password", timeout=180)
            self.child.sendline(pw)

            idx = self.child.expect(["Wrong Password or Username", self.any_prompt], timeout=600)
            if idx == 1:
                prompt = strip_ansi((self.child.after or "").strip())
                return prompt

            # wrong -> back to base prompt, restart lt all
            self.child.expect(self.base_prompt, timeout=180)
            self.child.sendline("lt all")
            self.child.expect("Please enter Username:", timeout=180)
            self.child.sendline(username)

        raise RuntimeError("Login failed: all passwords were rejected")
