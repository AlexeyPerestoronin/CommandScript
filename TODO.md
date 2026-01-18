# TODO:
- Поддержать возможность добавлять комментарий:
    - для отдельной команды:
        ```py
        commandcript.ScriptExecutor(ctx.script_dir, ctx.launch)\
            .add_command([f'command 1'], comment='1st command message')\
            .add_command([f'command 2'], comment='2nd command message')\
            .execute(log='single_comand_with_comment.log')
        ```
    - для блока команд:
        ```py
        commandcript.ScriptExecutor(ctx.script_dir, ctx.launch)\
            .add_commands([
                    [f'command 1'],
                    [f'command 2'],
                ],
                comment='block-command message')\
            .execute(log='multyple_comand_with_comment.log')
        ```
