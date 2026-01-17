import os
import invoke
import pathlib
import src.commandcript as commandcript
from src.commandcript import ENV_CONTEXT


ENV_CONTEXT\
    .add_env_var('PROJECT_GIT_DIR', f'{__file__}/../')\
    .add_env_var('COMMANDSCRIPT_SCRIPT_DIR', f'{ENV_CONTEXT.PROJECT_GIT_DIR}/.generated')\
    .add_env_var('PROJECT_DIST_DIR', f'{ENV_CONTEXT.PROJECT_GIT_DIR}/dist')


@commandcript.script_task()
def get_info(ctx):
    """
    Print to console information about active configuration of invoke-tasks
    """
    from prettytable import PrettyTable

    table = PrettyTable()
    table.align = "l"
    table.field_names = ["ENV-name", "ENV-value"]
    for key, value in ENV_CONTEXT.items():
        table.add_row([key, value])

    commandcript.INFO\
        .log_line("Active environment configuration:") \
        .log_line(f"{table}")


@commandcript.script_task(
    help={
        'cwd': 'working directory for yapf python files (by default: ENV_CONTEXT["PROJECT_GIT_DIR"])',
        'style-yapf': 'path to the .style.yapf (by default: ENV_CONTEXT["PROJECT_GIT_DIR"]/.style.yapf)',
        'dirs': 'list of directories where python files should be discovering (by default: ["./"])',
    },
    iterable=['dirs'])
def yapf(ctx, cwd: str = f'{ENV_CONTEXT.PROJECT_GIT_DIR}', style_yapf: str = f'{ENV_CONTEXT.PROJECT_GIT_DIR}/.style.yapf', dirs: list = None):
    """
    Format python files with script-tasks
    """

    def collect_file(dir):
        files = []
        for item in os.listdir(dir):
            item = pathlib.Path(os.path.join(f'{dir}', item))
            if item.is_file():
                if item.name.endswith('.py'):
                    files.append(f'"{item.as_posix()}"')
            elif item.is_dir():
                if not item.name.startswith('.'):
                    files.extend(collect_file(f'{item.as_posix()}'))
        return files

    if not dirs:
        dirs = ['./']

    for dir in dirs:
        log_file = 'yapf_' + '-'.join('/'.split(dir))
        log_file = log_file.replace('.', '')
        commandcript.ScriptExecutor(ctx.script_dir, ctx.launch)\
            .add_cwd(cwd)\
            .add_command([
                    f'yapf',
                    f'--style {style_yapf}',
                    f'--verbose',
                    f'--in-place',
                    *collect_file(f'{cwd}/{dir}')
                ])\
            .execute(log=log_file)


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
        dist_dir = ENV_CONTEXT['PROJECT_DIST_DIR']
        for filename in os.listdir(dist_dir):
            file_path = os.path.join(dist_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                commandcript.INFO.log_line(f'Deleted dist: {file_path}')

    commandcript.ScriptExecutor(ctx.script_dir, ctx.launch)\
        .add_cwd(ENV_CONTEXT['PROJECT_GIT_DIR'])\
        .add_command([f'pip install --upgrade build'] if install_build_tool else None)\
        .add_command([f'python -m build'])\
        .execute(log='prepare_build.log')


@commandcript.script_task(
    help={
        'install-uploading-tool': 'need to install python build tool before (by default: False)',
        'upload-on-test': 'if True, upload prepared package on https://test.pypi.org/; if False - on https://pypi.org/ (by default: True)',
    })
def publish_build(ctx, install_uploading_tool: bool = False, upload_on_test: bool = True):
    """
    Uploading build on PyPl
    """
    script = commandcript.ScriptExecutor(ctx.script_dir, ctx.launch).add_cwd(ENV_CONTEXT['PROJECT_GIT_DIR'])
    if install_uploading_tool:
        script.add_command([f'pip install --upgrade twine'])
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
