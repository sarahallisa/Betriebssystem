from pathlib import Path
from typing import List, Optional


class SubprocessResult:
    def __init__(self, command: str, result_code: Optional[int] = None, timedout: bool = False, stdout: Optional[str] = None, stderr: Optional[str] = None):
        self.command = command
        self.result = result_code
        self.stdout = stdout
        self.stderr = stderr
        self.timedout = timedout

    def is_success(self) -> bool:
        return self.result == 0 and not self.timedout

    def throw_if_timeout(self) -> 'SubprocessResult':
        if self.timedout:
            raise Exception("'%s' timed out!'" % self.command)
        else:
            return self

    def throw_if_failure(self) -> 'SubprocessResult':
        self.throw_if_timeout()
        if not self.is_success():
            raise Exception("'%s' failed (Exit code %d)!'" % (self.command, self.result))
        else:
            return self


def execute_subprocess(command: List[str], cwd: Optional[Path] = None, timeout: Optional[int] = None,
                       capture_output: bool = True, stdin: Optional[str] = None, is_shell_command: bool = False,
                       merge_stdout_stderr: bool = False) -> SubprocessResult:
    import subprocess

    command_str = " ".join(command)

    try:
        # With Python 3.7 we can use the capture_output and text parameters here
        result = subprocess.run(command, cwd=None if cwd is None else str(cwd), timeout=timeout, shell=is_shell_command,
                                stdout=subprocess.PIPE if capture_output else None,
                                stderr=subprocess.STDOUT if merge_stdout_stderr else (subprocess.PIPE if capture_output else None),
                                encoding="utf-8", input=stdin)

        return SubprocessResult(command_str, result.returncode, stdout=result.stdout, stderr=result.stderr)
    except subprocess.TimeoutExpired as result:
        return SubprocessResult(command_str, timedout=True,
                                stdout=result.stdout,
                                stderr=result.stderr)
