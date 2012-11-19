import os
import sys

from paste.script.serve import ServeCommand

from octomotron.utils import get_default_config


def config_parser(name, subparsers):
    parser = subparsers.add_parser(
        name, help='Serve the Octomotron application.')
    parser.set_defaults(func=serve, parser=parser)


def serve(args):
    if args.config is None:
        args.config = get_default_config()
    os.environ['PASTE_CONFIG_FILE'] = args.config

    cmd = ServeCommand('octomotron serve')
    exit_code = cmd.run([])
    sys.exit(exit_code)
