import os
import subprocess


class BatchExecutor:

    def __init__(self):
        pass

    def _create_batch_script(self, command, cwd: str, env: dict):
        script_lines = ["@echo off\n"]
        script_lines.append("\nsetlocal enabledelayedexpansion\n")

        script_lines.append('\n')

        if env:
            script_lines.append('\n')
            for k, v in env.items():
                script_lines.append(f'\nset "{k}={str(v)}"')

        if cwd:
            script_lines.append(f'\n\ncd /d "{cwd}"')

        # write each command on a new line, check return code after each
        for cmd in command:
            cmd_str = " ".join([str(arg) for arg in cmd])
            script_lines.append(f'\n\n{cmd_str}')
            script_lines.append('\nif errorlevel 1 goto :error')

        script_lines.append('\n\n:error')
        script_lines.append('\nset "ret=%errorlevel%"')
        script_lines.append('\necho === Return code: !ret! ===')
        script_lines.append('\nexit /b !ret!')
        return script_lines

    def _create_executed_script(self, command, cwd: str, env: dict, script_path: str):
        script_lines = self._create_batch_script(command, cwd, env)
        with open(script_path, "w", encoding="utf-8") as script_file:
            script_file.writelines(script_lines)
        os.chmod(script_path, 0o755)

    def get_execute_process_handler(self, command: list, *, cwd: str = None, env: dict = None, log_path: str = None):
        script_path = log_path.with_suffix('.bat')
        self._create_executed_script(command, cwd, env, script_path)
        process_handler = subprocess.Popen(
            ["cmd.exe", "/c", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding="utf-8",
            errors='replace',
            cwd=cwd,
            env=os.environ,
        )
        return [process_handler, script_path]
