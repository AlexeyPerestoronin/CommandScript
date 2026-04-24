import os
import invoke
import pathlib
import src.commandcript as commandcript


commandcript.ENV_CONTEXT\
    .add_env_var('COMMANDSCRIPT_SCRIPT_DIR', str(pathlib.Path(f'{__file__}').parent / '.generated'))\
    .add_env_var('PROJECT_GIT_DIR', str(pathlib.Path(f'{__file__}').parent))\
    .add_env_var('PROJECT_SRC_DIR', '${PROJECT_GIT_DIR}/src')\
    .add_env_var('PROJECT_DIST_DIR', '${PROJECT_GIT_DIR}/dist')


@commandcript.script_task()
def get_info(ctx):
    """
    Print to console information about active configuration of commandcript-tasks
    """
    names = [value.name for value in commandcript.ENV_CONTEXT.values()]
    hold_values = [value.hld for value in commandcript.ENV_CONTEXT.values()]
    expanded_values = [value.exp for value in commandcript.ENV_CONTEXT.values()]
    width = max(max(len(key) for key in names), max(len(item) for item in hold_values), max(len(item) for item in expanded_values), 25)
    commandcript.INFO.log_line("Active environment configuration:")
    commandcript.INFO.log_line(f"| {'Env-var name':<{width}} | {'Env-var hold-value':<{width}} | {'Env-var expanded-value':<{width}} |")
    commandcript.INFO.log_line(f"|-{'-' * width}-|-{'-' * width}-|-{'-' * width}-|")
    for i in range(len(names)):
        key = names[i]
        hold_value = hold_values[i]
        expanded_value = expanded_values[i]
        if expanded_value == hold_value:
            expanded_value = '-'
        commandcript.INFO.log_line(f"| {key:<{width}} | {hold_value:<{width}} | {expanded_value:<{width}} |")


@commandcript.script_task()
def yapf(ctx):
    """
    Format python files in Fuzz
    """
    commandcript.ScriptExecutor(ctx.script_dir, ctx.launch)\
        .add_cwd(commandcript.ENV_CONTEXT.PROJECT_GIT_DIR)\
        .add_command([
                "yapf",
                "--style .style.yapf",
                "--verbose",
                "--recursive",
                "--in-place",
                "--parallel",
                f"--exclude '**.venv**'",
                f"{commandcript.ENV_CONTEXT.PROJECT_SRC_DIR}",
            ])\
        .execute(log="yapf.log")


@commandcript.script_task(
    help={
        'install-build-tool': 'need to install python build tool before (by default: False)',
        'clean-dist': 'clean folder with distributive (by default: False)'
    })
def prepare_build(ctx, install_build_tool: bool = False, clean_dist=False):
    """
    Prepare build before uploading on PyPl
    """
    if clean_dist:
        dist_dir = pathlib.Path(commandcript.ENV_CONTEXT.PROJECT_DIST_DIR.exp)
        if dist_dir.exists():
            for filename in os.listdir(dist_dir):
                file_path = os.path.join(dist_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    commandcript.INFO.log_line(f'Deleted dist: {file_path}')

    commandcript.ScriptExecutor(ctx.script_dir, ctx.launch)\
        .add_cwd(commandcript.ENV_CONTEXT.PROJECT_GIT_DIR.hld)\
        .add_command([f'pip install --upgrade build'] if install_build_tool else None)\
        .add_command([f'python -m build'])\
        .execute(log='prepare_build.log')


@commandcript.script_task(
    help={
        'upload-on-test': 'if True, upload prepared package on https://test.pypi.org/; if False - on https://pypi.org/ (by default: True)',
    })
def publish_build(ctx, upload_on_test: bool = True):
    """
    Uploading build on PyPl
    """
    script = commandcript.ScriptExecutor(ctx.script_dir, ctx.launch).add_cwd(commandcript.ENV_CONTEXT.PROJECT_GIT_DIR.hld)
    if upload_on_test:
        script.add_command([f'python -m twine upload --verbose --repository testpypi dist/*'])
        script.execute(log='publish_on_testpypi.log')
    else:
        script.add_command([f'python -m twine upload --verbose dist/*'])
        script.execute(log='publish_on_pypi.log')


@commandcript.script_task(help={
    'upload-on-test': 'if True, upload prepared package on https://test.pypi.org/; if False - on https://pypi.org/ (by default: True)',
})
def full_pipeline(ctx, upload_on_test: bool = True):
    """
    Yafp & Building & Uploading on PyPl
    """
    yapf(ctx, script_dir=ctx.script_dir, launch=ctx.launch)
    prepare_build(ctx, script_dir=ctx.script_dir, launch=ctx.launch, clean_dist=True)
    publish_build(ctx, script_dir=ctx.script_dir, launch=ctx.launch, upload_on_test=upload_on_test)


namespace = invoke.Collection()
namespace.add_task(get_info, name="get-info")
namespace.add_task(yapf, name="yapf")
namespace.add_task(prepare_build, name="prepare-build")
namespace.add_task(publish_build, name="publish_build")
namespace.add_task(full_pipeline, name="full-pipeline")
