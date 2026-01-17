# CommandScript

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

CommandScript is a Python library that provides utilities for task management through the creation and execution of OS-specific scripts. It simplifies cross-platform command execution by generating shell scripts (.sh for Unix-like systems, .bat for Windows) and handling logging, timing, and error checking automatically.

Based on the [invoke](https://www.pyinvoke.org/) library, it allows you to create collections of tasks running along the following pipeline:

![](./pipeline.drawio.png)

## Features

- **Cross-platform script execution**: Automatically generates and executes OS-specific scripts (Bash for Linux/macOS, Batch for Windows)
    - ⚠️ MacOS (NOT TESTED)
    - ✅ Linux (POSIX)
        - Generates `.sh` Bash scripts
        - Uses `bash` for execution
        - Supports shell quoting and escaping
        - Measures execution time with nanosecond precision
    - ✅ Windows (NT)
        - Generates `.bat` Batch scripts
        - Uses `cmd.exe` for execution
        - Handles Windows path separators and quoting
        - Supports delayed variable expansion
- **Task management**: Built-in support for Invoke tasks with decorators
    - each task you launch:
        - will collect its log twice: in console and special file (defined for the task unique)
        - if managed via `ScriptExecutor` will has two files for yourself:
            1. script file: `path/to/.generated/your-script-task.(sh|bat)`
            2. script logs: `path/to/.generated/your-script-task.log`
     - when task is finished:
         - its script is saved and could be launch via terminal directly
         - its execution log is saved and could be open in IDE for analytics
- **Environment context**: Global environment variable management for script execution
- **Integrated logging**: Colored console output and file logging with timestamps
- **Error handling**: Automatic return code checking and exception raising on failures
- **Timing**: Execution duration measurement for performance monitoring

## Installation

Install CommandScript using pip:

```bash
pip install commandcript
```

### Dependencies

CommandScript requires the following dependencies (automatically installed):

- `invoke>=2.2.0` - Task execution framework
- `colorama>=0.4.6` - Cross-platform colored terminal text
- `prettytable>=3.17.0` - Display tabular data

## Quick Start

✅ Good practice example you can see in [tasks.py](https://github.com/AlexeyPerestoronin/CommandScript/blob/master/tasks.py)

### Basic Usage

```python
import os
import commandcript

# Set up environment context
commandcript.ENV_CONTEXT.update({
    'PROJECT_GIT_DIR': '/path/to/project',
    'COMMANDSCRIPT_SCRIPT_DIR': '/path/to/scripts'
})

# Create and execute a simple command
executor = commandcript.ScriptExecutor(
    log_dir='/path/to/logs',
    execute_created_script=True
)

executor.add_cwd('/path/to/working/directory') \
        .add_command(['echo', 'Hello, World!']) \
        .execute(log='hello_world')
```

### Using with Invoke Tasks

```python
import invoke
import commandcript

commandcript.ENV_CONTEXT.add_env_var('COMMANDSCRIPT_SCRIPT_DIR', '/path/to/folder/with/generated/scripts/.generated')

# Define a task
@scommandcript.cript_task()
def build(ctx):
    """Build the project"""
    commandcript.ScriptExecutor(ctx.script_dir, ctx.launch) \
        .add_cwd(ENV_CONTEXT.PROJECT_GIT_DIR) \
        .add_command(['python', 'setup.py', 'build']) \
        .execute(log='build')

# Create namespace and run
namespace = invoke.Collection()
namespace.add_task(build)
```

### Environment Setup
`commandcript.ENV_CONTEXT` is a global instance of the `EnvContext` class, which is a specialized dictionary for storing environment variables and paths used across `@commandcript.script_task()` instances.

The `EnvContext` class provides additional functionality for managing environment variables, including the `add_env_var` method for retrieving OS environment variables with defaults and automatic path conversion.

Before using CommandScript, set up the environment context:

```python
from src.commandcript import ENV_CONTEXT

ENV_CONTEXT\
    .add_env_var('PROJECT_GIT_DIR', f'{__file__}/../')\
    .add_env_var('COMMANDSCRIPT_SCRIPT_DIR', f'{ENV_CONTEXT.PROJECT_GIT_DIR}/.generated')\
    .add_env_var('PROJECT_DIST_DIR', f'{ENV_CONTEXT.PROJECT_GIT_DIR}/dist')
```

### Multi-command execution

```python
import commandcript

executor = commandcript.ScriptExecutor('/path/to/logs', True)

executor.add_cwd('/tmp') \
        .add_env({'MY_VAR': 'value'}) \
        .add_command(['export', 'MY_VAR=override']) \
        .add_command(['echo', '$MY_VAR']) \
        .add_command(['ls', '-la']) \
        .execute(log='multi_command')
```

### Task with Parameters

```python
@commandcript.script_task(
    help={
        'target': 'Build target (default: all)',
        'clean': 'Clean before build'
    }
)
def build(ctx, target='all', clean=False):
    executor = commandcript.ScriptExecutor(ctx.script_dir, ctx.launch)

    if clean:
        executor.add_command(['make', 'clean'])

    executor.add_command(['make', target]) \
            .execute(log=f'build_{target}')
```

## API Reference

### ScriptExecutor

The main class for executing commands via OS-specific scripts.

- **Constructor**:
    ```python
    ScriptExecutor(log_dir: str, execute_created_script: bool)
    ```
    - `log_dir`: Directory where log files and scripts will be stored
    - `execute_created_script`: If True, executes the generated script; if False, only generates it
- **Methods**
    - `add_cwd(cwd: str)`: Set working directory for script execution
    - `add_env(env: dict)`: Add environment variables
    - `add_command(command: list, enter=True, offset=True)`: Add a single command
    - `add_commands(commands: list, enter=True, offset=True)`: Add multiple commands
    - `execute(log: str = None)`: Execute the script and log output

### @script_task()

Decorator for defining Invoke tasks with CommandScript integration.

```python
@commandcript.script_task(
    help={'param': 'Description'},
    iterable=['param']
)
def my_task(ctx, param=None):
    # Task implementation
    pass
```

### Logging

CommandScript provides colored logging utilities:

- `INFO`: General information (blue)
- `SUCCESS`: Success messages (green)
- `STATUS`: Status updates (cyan)
- `ERROR`: Error messages (red)

```python
import commandcript

commandcript.INFO.log_line("This is an info message")
commandcript.SUCCESS.log_line("Operation completed successfully")
commandcript.ERROR.log_line("An error occurred")
```