from ...configuration.utilities import enable_yaml_load
from ...exceptions.executorexceptions import CommandExecutionFailure
from ...interfaces.executor import Executor
from ..attributedict import AttributeDict

import asyncio


@enable_yaml_load("!ShellExecutor")
class ShellExecutor(Executor):
    def __init__(self, *args, **kwargs):
        pass

    async def run_command(self, command, stdin_input=None):
        sub_process = await asyncio.create_subprocess_shell(
            command,
            stdin=stdin_input and asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await sub_process.communicate(
            stdin_input and stdin_input.encode()
        )
        exit_code = sub_process.returncode

        # Potentially due to a Python bug, if waitpid(0) is called somewhere else,
        # the message "WARNING:asyncio:Unknown child process pid 2960761,
        # will report returncode 255 appears"
        # However the command succeeded
        if not exit_code or exit_code == 255:
            return AttributeDict(
                stdout=stdout.decode().strip(),
                stderr=stderr.decode().strip(),
                exit_code=exit_code,
            )
        else:
            raise CommandExecutionFailure(
                message=f"Run command {command} via ShellExecutor failed",
                exit_code=exit_code,
                stdout=stdout.decode().strip(),
                stderr=stderr.decode().strip(),
                stdin=stdin_input,
            )
