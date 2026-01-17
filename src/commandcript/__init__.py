"""
Command Script Module - Python utilities for task management by creation and execution OS-specific scripts.

This module provides a framework for creating and executing OS-specific scripts
(shell scripts on Unix/Linux, PowerShell scripts on Windows) through the invoke
task library. It includes utilities for:

- Creating cross-platform script execution tasks
- Logging with colored output
- Managing environment context for tasks
- Constructing OS-specific path strings

Main Components:
    - script_task: A decorator factory for creating invoke tasks with automatic
                   script management and documentation
    - ScriptExecutor: A class for building and executing OS-specific scripts
    - Logger instances (SUCCESS, STATUS, INFO, WARNING, ERROR): Colored logging utilities
    - join_env_paths: Helper for joining env-paths with OS-specific separators

Usage Example:
    @script_task()
    def my_task(ctx, name):
        '''My task description.'''
        ScriptExecutor(ctx.script_dir, ctx.launch)\
            .add_command(["echo", f"Hello, {name}"])\
            .execute(log="my-task.log")

    # Invoke with: invoke my-task --name "World"

See Also:
    - APTTasks/commandscipt/script_executor.py: ScriptExecutor implementation
    - APTTasks/commandscipt/logger.py: Logger implementation
"""

import inspect
import functools

from .env_context import ENV_CONTEXT
from .script_executor import ScriptExecutor
from .logger import SUCCESS, STATUS, INFO, WARNING, ERROR


def join_env_paths(paths: list) -> str:
    """
    Join a list of environment paths into a single string using OS-specific separator.

    Args:
        paths: A list of path strings to be joined together.

    Returns:
        str: A single string containing all paths joined by the appropriate
             separator. Uses semicolon (';') for Windows (os.name == "nt")
             and colon (':') for Unix-like systems (Linux, macOS).

    Example:
        >>> # On Unix/Linux:
        >>> join_env_paths(['/path/to/bin', '/usr/local/bin'])
        '/path/to/bin:/usr/local/bin'

        >>> # On Windows:
        >>> join_env_paths(['C:\\path\\to\\bin', 'D:\\usr\\local\\bin'])
        'C:\\path\\to\\bin;D:\\usr\\local\\bin'
    """
    import os
    if os.name == "nt":
        separator = ';'
    else:
        separator = ':'
    return separator.join(paths)


def print_task_documentation(func):

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        doc = func.__doc__
        if doc:
            STATUS.log_line(doc.strip())
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            if bound_args.arguments:
                STATUS.log_line("Parameters:")
                for name, value in [item for item in bound_args.arguments.items()][1:]:
                    STATUS.log_line(f" * {name}: {value}")
        return func(*args, **kwargs)

    return decorator


import invoke


def script_task(**task_kwargs):
    """
    A decorator factory for creating invoke tasks with automatic script management.

    This decorator simplifies the creation of invoke tasks that use ScriptExecutor
    for running OS-specific scripts. It automatically adds two keyword-only parameters
    to the decorated function: 'script_dir' and 'launch', which are then attached
    to the invoke context object.

    The decorator wraps the original function with:
    1. Automatic documentation printing via print_task_documentation
    2. Script directory and launch mode configuration via context attributes

    Args:
        **task_kwargs: Additional keyword arguments passed to invoke.task().
                       Common options include 'name', 'help', 'default', etc.

    Returns:
        A decorator function that can be applied to task functions.

    Example:
        @script_task()
        def build_project(ctx, config="release"):
            '''Build the project with the specified configuration.'''
            ScriptExecutor(ctx.script_dir, ctx.launch)\
                .add_command(["make", f"CONFIG={config}"])\
                .execute(log="build.log")

        # The task now automatically accepts:
        # - config (positional/keyword arg from function signature)
        # - script_dir (keyword-only, defaults to ENV_CONTEXT value)
        # - launch (keyword-only, defaults to True)

        # Usage:
        # inv build-project --script-dir /tmp/scripts --launch config=debug

    Note:
        The 'script_dir' parameter can be overridden via:
        1. Explicit --script-dir argument when invoking the task
        2. ENV_CONTEXT['COMMANDSCRIPT_SCRIPT_DIR'] environment variable
        3. ENV_CONTEXT environment variable (fallback)
    """
    import os

    def decorator(func):
        sig = inspect.signature(func)

        # check if 'script_dir' is already defined in the signature
        if 'script_dir' in sig.parameters:
            raise ValueError(f"Function {func.__name__} already has parameter 'script-dir' (user another name for your parameter)")

        # check if 'launch' is already defined in the signature
        if 'launch' in sig.parameters:
            raise ValueError(f"Function {func.__name__} already has parameter 'launch' (user another name for your parameter)")

        # create new function with new parameters
        @functools.wraps(func)
        def wrapper(ctx, *args, script_dir: str, launch: bool, **kwargs):
            if not script_dir:
                raise ValueError(f"parameter `script-dir` isn't defined (define it via ENV_CONTEXT['COMMANDSCRIPT_SCRIPT_DIR'] or env-COMMANDSCRIPT_SCRIPT_DIR))")
            setattr(ctx, 'script_dir', script_dir)
            setattr(ctx, 'launch', launch)
            # call original function
            return func(ctx, *args, **kwargs)

        # update function signature with new parameters
        script_dir_default_value = ENV_CONTEXT.get('COMMANDSCRIPT_SCRIPT_DIR', os.environ.get('ENV_CONTEXT'))
        wrapper.__signature__ = sig.replace(
            parameters=[
                *sig.parameters.values(),
                inspect.Parameter('script_dir', inspect.Parameter.KEYWORD_ONLY, default=script_dir_default_value, annotation=str),
                inspect.Parameter('launch', inspect.Parameter.KEYWORD_ONLY, default=True, annotation=bool),
            ])

        # create new help with two common parameters: script-dir and launch
        new_help = {
            "script-dir": "path to the directory where new script should be created (by default: ENV_CONTEXT['COMMANDSCRIPT_SCRIPT_DIR'] or env-COMMANDSCRIPT_SCRIPT_DIR)",
            "launch": "should launch created script or just create (by default: True)",
            **task_kwargs.get('help', {})  # save original help
        }

        return invoke.task(**{**task_kwargs, 'help': new_help})(print_task_documentation(wrapper))

    return decorator


__all__ = [
    # logging
    "SUCCESS",
    "STATUS",
    "INFO",
    "WARNING",
    "ERROR",
    # scrip creation
    "ENV_CONTEXT",
    "ScriptExecutor",
    "script_task",
    # support functions
    "join_env_paths",
]
