#!/usr/bin/python3 -I
"""Install the reviewed host launcher and exact sudo rule; do not change groups."""

import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


CONFIG = b"""default-remote: local
remotes:
  local:
    addr: unix://
    protocol: incus
    public: false
aliases: {}
"""
LAUNCHER = Path("/usr/local/sbin/dev-box-enter")
POLICY = Path("/etc/sudoers.d/dev-box-enter")
CONFIG_DIR = Path("/etc/dev-box-launcher")
SAFE_ENV = {"HOME": "/root", "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}


def trusted_directory(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
        raise RuntimeError(f"Expected a root-owned directory not writable by others: {path}")


def previous_file(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
        raise RuntimeError(f"Refusing to replace an untrusted file or symlink: {path}")
    return path.read_bytes(), stat.S_IMODE(info.st_mode), info.st_gid


def replace_file(path, contents, mode, group=0):
    descriptor, temporary = tempfile.mkstemp(prefix=".dev-box-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(contents)
            output.flush()
            os.fchown(output.fileno(), 0, group)
            os.fchmod(output.fileno(), mode)
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def check_sudoers(path=None):
    arguments = ["/usr/bin/visudo", "-cq"]
    if path is not None:
        arguments.extend(["-f", str(path)])
    result = subprocess.run(arguments, env=SAFE_ENV, capture_output=True)
    if result.returncode:
        raise RuntimeError("Sudoers validation failed; no invalid policy will be left installed.")


def main():
    if len(sys.argv) != 1:
        raise RuntimeError("This installer accepts no arguments.")
    if os.geteuid() != 0:
        raise RuntimeError("Run this installer with sudo or pkexec.")
    source = Path(__file__).resolve().parent
    launcher = (source / "dev-box-enter").read_bytes()
    policy = (source / "dev-box-enter.sudoers").read_bytes()
    compile(launcher, str(LAUNCHER), "exec")
    os.chdir("/")
    os.umask(0o077)

    for parent in [Path("/"), Path("/usr"), Path("/usr/local"), LAUNCHER.parent,
                   Path("/etc"), POLICY.parent]:
        trusted_directory(parent)
    check_sudoers()
    with tempfile.TemporaryDirectory(prefix="dev-box-policy-", dir="/var/tmp") as stage:
        candidate = Path(stage) / "sudoers"
        candidate.write_bytes(policy)
        check_sudoers(candidate)

    created_directory = not CONFIG_DIR.exists() and not CONFIG_DIR.is_symlink()
    if created_directory:
        CONFIG_DIR.mkdir(mode=0o700)
    trusted_directory(CONFIG_DIR)
    files = [
        (CONFIG_DIR / "config.yml", CONFIG, 0o600),
        (LAUNCHER, launcher, 0o755),
        (POLICY, policy, 0o440),
    ]
    previous = {path: previous_file(path) for path, _, _ in files}
    installed = []
    try:
        for path, contents, mode in files:
            replace_file(path, contents, mode)
            installed.append(path)
        check_sudoers()
    except BaseException:
        for path in reversed(installed):
            original = previous[path]
            if original is None:
                path.unlink()
            else:
                replace_file(path, *original)
        if created_directory:
            CONFIG_DIR.rmdir()
        raise
    print("Installed restricted dev-box launcher and validated sudo policy.")
    print("Group memberships, containers, mounts, and services were not changed.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as error:
        print(f"Installation failed: {error}", file=sys.stderr)
        sys.exit(1)
