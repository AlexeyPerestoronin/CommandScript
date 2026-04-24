import os
import re

from typing import Dict


class EnvVariable:
    """
    Presents one evn-variable.
    """

    def __init__(self, env_var_name: str, env_var_dirty_value: str):
        if os.name == "nt":
            open_symbol = '%'
            close_symbol = '%'
        elif os.name == "posix":
            open_symbol = '$'
            close_symbol = ''
        else:
            raise Exception("unsupported operation system!")

        env_var_hold_value = str(env_var_dirty_value)
        env_var_expanded_value = str(env_var_dirty_value)
        sub_var_pattern = re.compile(r'(\$\{(.+?)\})')
        substitution_patterns = re.findall(sub_var_pattern, env_var_expanded_value)
        for substitution_pattern in substitution_patterns:
            substitution_value = ENV_CONTEXT.get(substitution_pattern[1])
            if not substitution_value:
                raise Exception(f"env-variable '{env_var_name}' has unregistered substitution pattern '{substitution_pattern}'")
            env_var_hold_value = env_var_hold_value.replace(substitution_pattern[0], f"{open_symbol}{substitution_pattern[1]}{close_symbol}")
            env_var_expanded_value = env_var_expanded_value.replace(substitution_pattern[0], substitution_value.exp)

        self.__name = env_var_name
        self.__hold_value = env_var_hold_value
        self.__expanded_value = env_var_expanded_value

    @property
    def name(self) -> str:
        return self.__name

    @property
    def hld(self) -> str:
        return self.__hold_value

    @property
    def exp(self) -> str:
        return self.__expanded_value

    def __str__(self) -> str:
        return self.hld


class EnvContext(Dict[str, EnvVariable]):
    """
    EnvContext is a specialized dictionary class for managing environment variables in the CommandScript library.
    """

    def add_env_var(self, env_var_name: str, default_value: str = None) -> 'EnvContext':
        """
        Add an environment variable from OS environment with fallback to default value.

        Args:
            env_var_name: Name of the environment variable to read
            default_value: Default value to use if env variable is not set
            as_path: If True, treat the value as a file path and convert to absolute path

        Returns:
            EnvContext: Self for method chaining

        Raises:
            Exception: If env variable is not set and no default_value provided

        Notes:
            Added values will be available as EnvContext member: ENV_CONTEXT.'env_var_name'
        """
        env_var_value = os.environ.get(env_var_name)
        if not env_var_value:
            if default_value is not None:
                env_var_value = default_value
            else:
                raise Exception(f"env-variable {env_var_name} is not set!")

        env_var_value = EnvVariable(env_var_name, env_var_value)
        setattr(self, env_var_name, env_var_value)
        self[env_var_name] = env_var_value
        return self


ENV_CONTEXT = EnvContext()
