import os
import subprocess


class BashExecutor:

    def __init__(self):
        pass

    def _create_bash_script(self, command, cwd: str, env: dict):

        def shlex_quote(s):
            """Safely quotes a string for passing to a shell command."""
            import shlex
            return shlex.quote(s)

        script_lines = ["#!/bin/bash\n"]

        if env:
            for k, v in env.items():
                script_lines.append(f"export {k}={shlex_quote(str(v))}\n")

        if cwd:
            script_lines.append(f"\ncd {shlex_quote(cwd)}\n")

        script_lines.append('\nstart_time=$(date +%s.%N)\n')
        # Write each command on a new line, check return code after each
        for cmd in command:
            cmd_str = " ".join([arg for arg in cmd])
            script_lines.append(f"\n{cmd_str}; ret=$?\n")
            script_lines.append(f"if [ $ret -ne 0 ]; then exit $ret; fi\n")
        script_lines.append('\nend_time=$(date +%s.%N)\n')
        script_lines.append('\nduration=$(echo "$end_time - $start_time" | bc)\n')
        script_lines.append('\nexit $ret\n')
        return script_lines

    def _create_executed_script(self, command, cwd: str, env: dict, script_path: str):
        script_lines = self._create_bash_script(command, cwd, env)
        with open(script_path, "w", encoding="utf-8") as script_file:
            script_file.writelines(script_lines)
        os.chmod(script_path, 0o755)

    def get_execute_process_handler(self, command: list, *, cwd: str = None, env: dict = None, log_path: str = None):
        script_path = log_path.with_suffix('.sh')
        self._create_executed_script(command, cwd, env, script_path)
        process_handler = subprocess.Popen(
            ["bash", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=cwd,
            env=os.environ,
        )
        return [process_handler, script_path]
