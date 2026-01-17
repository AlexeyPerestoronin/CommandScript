import os
import pathlib
import threading
import time
import copy
import typing

from .logger import SUCCESS, STATUS, ERROR, INFO
from .env_context import ENV_CONTEXT


class ScriptExecutor:
    """
    This class is used to execute commands via OS specific scripting file:
    1) *.sh - in unix system like Ubuntu;
    2) *.ps1 - in windows system since Windows-10;
    Also, when command is executing their log will output in both sources:
    1) to the standard output;
    2) to the corresponded log file.
    Additionally, this class checks the return code of executed operation and measures the time duration of its execution.
    """

    def __init__(self, log_dir: str, execute_created_script: bool):
        self.__log_dir = log_dir
        self.__execute_created_script = execute_created_script
        if os.name == "nt":
            from . import windows
            self.__executor = windows.BatchExecutor()
        elif os.name == "posix":
            from . import ubuntu
            self.__executor = ubuntu.BashExecutor()
        else:
            raise Exception("unsupported operation system!")
        self.__cwd = None
        self.__env = copy.deepcopy(ENV_CONTEXT)
        self.__commands = []
        # create log directory if doesn't exist yet
        pathlib.Path(self.__log_dir).mkdir(parents=True, exist_ok=True)

    def add_cwd(self, cwd: str):
        self.__cwd = cwd
        return self

    def add_env(self, env: dict):
        self.__env |= env
        return self

    def add_command(self, command: list, *, enter=True, offset=True):
        offset = "    " if enter and offset else ""
        if os.name == "nt":
            enter = "^\n" if enter else ""
        elif os.name == "posix":
            enter = " \\\n" if enter else ""
        else:
            raise Exception("unsupported operation system!")

        if command:
            clean_command = [command_line for command_line in command if command_line is not None]
            format_command = [clean_command[0]]
            for command_line in clean_command[1:]:
                format_command.append(f"{enter}{offset}{command_line}")
            self.__commands.append(format_command)
        return self

    def add_commands(self, commands: list, *, enter=True, offset=True):
        for command in commands:
            self.add_command(command, enter=enter, offset=offset)
        return self

    def execute(self, log: str = None):
        log_path = pathlib.Path(f"{self.__log_dir}/{log}")
        [process_handler, script_path] = self.__executor.get_execute_process_handler(self.__commands, cwd=self.__cwd, env=self.__env, log_path=log_path)

        if self.__execute_created_script == False:
            STATUS \
                .log_line("\nWithout execution:") \
                .log_line(f"Command script file: {script_path}")
            return

        start_time = time.time()

        # open log-file for rewriting
        log_file = open(log_path, "w", encoding="utf-8")

        def write_log_line(line):
            # write in console
            INFO.log_line(f"{line.rstrip()}")
            # write in log-file
            log_file.write(f"{line}")
            log_file.flush()

        def read_stream(stream, stream_type):
            for line in stream:
                write_log_line(f"[{stream_type}] {line}")

        stdout_thread = threading.Thread(target=read_stream, args=(process_handler.stdout, "stdout"))
        stderr_thread = threading.Thread(target=read_stream, args=(process_handler.stderr, "stderr"))

        stdout_thread.start()
        stderr_thread.start()

        stdout_thread.join()
        stderr_thread.join()

        return_code = process_handler.wait()
        end_time = time.time()
        duration = end_time - start_time

        # write summary about execution-time and return-code
        summary = f"\n=== Duration: {duration:.3f} seconds ===\n=== Return code: {return_code} ===\n"
        write_log_line(summary)

        log_file.close()

        STATUS \
            .log_line(f"\nCommand script file: {script_path}") \
            .log_line(f"Command log file: {log_path}") \

        if return_code == 0:
            SUCCESS.log_line("Command completed successfully.")
        else:
            ERROR.log_line(f"Command failed: return code {return_code}.")
            raise Exception("command execution error!")
