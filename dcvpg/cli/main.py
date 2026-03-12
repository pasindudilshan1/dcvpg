import click
from .commands.init import init
from .commands.generate import generate
from .commands.validate import validate
from .commands.watch import watch
from .commands.register import register
from .commands.diff import diff
from .commands.status import status
from .commands.replay import replay
from .commands.mcp_server import mcp_server
from .commands.serve import serve


@click.group()
def cli():
    """
    Data Contract Validator & Pipeline Guardian (DCVPG)

    The open-source framework for validating pipelines against formal contracts.
    """
    pass


cli.add_command(init)
cli.add_command(generate)
cli.add_command(validate)
cli.add_command(watch)
cli.add_command(register)
cli.add_command(diff)
cli.add_command(status)
cli.add_command(replay)
cli.add_command(mcp_server, name="mcp-server")
cli.add_command(serve)
