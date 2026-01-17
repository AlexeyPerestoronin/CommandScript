import os
import typing
import pathlib


class EnvContext(typing.Dict[str, typing.Any]):
    """
    EnvContext is a specialized dictionary class for managing environment variables in the CommandScript library.
    """

    def add_env_var(self, env_var_name: str, default_value: str = None, *, as_path: bool = True) -> 'EnvContext':
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
        value = os.environ.get(env_var_name)
        if not value:
            if default_value is not None:
                value = default_value
            else:
                raise Exception(f"env-variable {env_var_name} is not set!")

        if as_path:
            value = pathlib.Path(os.path.abspath(value)).as_posix()

        setattr(self, env_var_name, value)
        self[env_var_name] = value
        return self


ENV_CONTEXT = EnvContext()
