import sys
import os

# Add framework to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dcvpg.cli.main import cli

if __name__ == '__main__':
    cli()
