"""Security boundary tests; no root access or container daemon is required."""

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "dev-box-enter"
loader = SourceFileLoader("dev_launcher", str(SOURCE))
spec = spec_from_loader(loader.name, loader)
launcher = module_from_spec(spec)
loader.exec_module(launcher)


class LauncherSecurityTests(unittest.TestCase):
    def test_only_the_host_home_boundary_is_mapped(self):
        for host, expected in [
            ("/home/kian", "/home/dev"),
            ("/home/kian/game/src", "/home/dev/game/src"),
            ("/home/kian-other/project", "/home/dev"),
            ("/etc", "/home/dev"),
        ]:
            with self.subTest(host=host):
                self.assertEqual(launcher.container_directory(host), expected)

    def test_hostile_directory_is_data_not_an_incus_option_or_shell_program(self):
        directory = "/home/kian/project '; $(touch /tmp/owned)\n--user=0"
        arguments, _ = launcher.invocation(directory, "xterm-kitty")
        boundary = arguments.index("--")
        self.assertEqual(arguments[arguments.index("--user") + 1], "1000")
        self.assertEqual(arguments[arguments.index("--group") + 1], "1000")
        self.assertEqual(arguments[arguments.index("--project") + 1], "default")
        self.assertEqual(arguments[arguments.index("exec") + 1], "node-dev")
        self.assertNotIn(directory, arguments[:boundary])
        self.assertEqual(arguments[-1], directory.replace("/home/kian", "/home/dev", 1))
        self.assertNotIn("touch", arguments[-3])

    def test_shell_does_not_evaluate_directory_contents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "space ' ; $(touch INJECTED)"
            directory.mkdir()
            environment = {"HOME": str(root), "PATH": "/usr/bin:/bin", "TERM": "dumb"}
            result = subprocess.run(
                ["/bin/bash", "--noprofile", "--norc", "-c", launcher.CONTAINER_ENTRY,
                 "dev-box-enter", str(directory)],
                input="unset HISTFILE\nprintf 'CWD=%s\\n' \"$PWD\"\nexit\n",
                text=True, capture_output=True, env=environment, cwd=root, timeout=10,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("CWD=" + str(directory), result.stdout)
            self.assertFalse((root / "INJECTED").exists())
            self.assertFalse((directory / "INJECTED").exists())

    def test_privileged_execution_replaces_environment_and_working_directory(self):
        hostile = {
            "HOME": "/tmp/attacker", "PATH": "/tmp/attacker",
            "PYTHONPATH": "/tmp/attacker", "BASH_ENV": "/tmp/attacker",
            "INCUS_CONF": "/tmp/attacker", "INCUS_GLOBAL_CONF": "/tmp/attacker",
            "INCUS_DIR": "/tmp/attacker", "INCUS_PROJECT": "other",
            "INCUS_REMOTE": "other:", "https_proxy": "http://attacker.invalid",
            "TERM": "tmux-256color", "PWD": "/home/kian/fake",
        }
        with patch.object(launcher.sys, "argv", [str(SOURCE)]), \
             patch.object(launcher.os, "geteuid", return_value=0), \
             patch.object(launcher.os, "getcwd", return_value="/home/kian/game"), \
             patch.object(launcher.os, "chdir") as chdir, \
             patch.object(launcher.os, "umask"), \
             patch.dict(launcher.os.environ, hostile, clear=True), \
             patch.object(launcher.os, "execve") as execute:
            launcher.main()
        chdir.assert_called_once_with("/")
        executable, arguments, environment = execute.call_args.args
        self.assertEqual(executable, "/usr/bin/incus")
        self.assertEqual(arguments[-1], "/home/dev/game")
        self.assertEqual(environment, {
            "HOME": "/root", "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
            "TERM": "tmux-256color", "INCUS_DIR": "/var/lib/incus",
            "INCUS_CONF": "/etc/dev-box-launcher",
            "INCUS_GLOBAL_CONF": "/etc/dev-box-launcher",
        })

    def test_invalid_terminal_names_cannot_add_environment_or_options(self):
        for terminal in ["", "xterm\nINCUS_DIR=/tmp", "--user=0", "x" * 65]:
            with self.subTest(terminal=terminal):
                arguments, environment = launcher.invocation("/home/kian", terminal)
                self.assertEqual(environment["TERM"], "xterm-256color")
                self.assertIn("TERM=xterm-256color", arguments)

    def test_extra_arguments_and_unprivileged_execution_fail_closed(self):
        with patch.object(launcher.sys, "argv", [str(SOURCE), "--user=0"]), \
             patch.object(launcher.os, "execve") as execute:
            self.assertEqual(launcher.main(), 2)
            execute.assert_not_called()
        with patch.object(launcher.sys, "argv", [str(SOURCE)]), \
             patch.object(launcher.os, "geteuid", return_value=1000), \
             patch.object(launcher.os, "execve") as execute:
            self.assertEqual(launcher.main(), 1)
            execute.assert_not_called()

    def test_deleted_host_directory_falls_back_to_container_home(self):
        with patch.object(launcher.sys, "argv", [str(SOURCE)]), \
             patch.object(launcher.os, "geteuid", return_value=0), \
             patch.object(launcher.os, "getcwd", side_effect=FileNotFoundError), \
             patch.object(launcher.os, "chdir"), patch.object(launcher.os, "umask"), \
             patch.object(launcher.os, "execve") as execute:
            launcher.main()
        self.assertEqual(execute.call_args.args[1][-1], "/home/dev")

    def test_isolated_interpreter_ignores_user_python_startup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / "executed"
            (root / "sitecustomize.py").write_text(
                "from pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\n"
            )
            result = subprocess.run(
                ["/usr/bin/python3", "-I", str(SOURCE), "rejected"],
                cwd=root, env={**os.environ, "PYTHONPATH": str(root)},
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
