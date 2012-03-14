import argparse
import logging
import os
import pkg_resources
import sys

from octomotron.exc import UserError


OCTOMOTRON_CFG = '.octomotron.cfg'

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s')


def main(argv=sys.argv, out=sys.stdout):
    parser = argparse.ArgumentParser()
    parser.add_argument('-C', '--config', metavar='FILE', default=None,
                        help='Path to configuration ini file.')

    subparsers = parser.add_subparsers(
        title='command', help='Available commands.')
    eps = [ep for ep in pkg_resources.iter_entry_points('octomotron.script')]
    eps.sort(key=lambda ep: ep.name)
    ep_names = set()
    for ep in eps:
        if ep.name in ep_names:
            raise RuntimeError('script defined more than once: %s' % ep.name)
        ep_names.add(ep.name)
        ep.load()(ep.name, subparsers)

    args = parser.parse_args(argv[1:])
    if args.config is None:
        args.config = get_default_config()
    try:
        args.func(args)
    except UserError, e:
        args.parser.error(str(e))


def get_default_config():
    config = 'octomotron.ini'

    if os.path.exists(config):
        return os.path.abspath(config)

    bin = os.path.abspath(sys.argv[0])
    env = os.path.dirname(os.path.dirname(bin))
    config = os.path.join(env, 'etc', 'octomotron.ini')

    if os.path.exists(config):
        return config

    config = os.path.join('etc', 'octomotron.ini')

    if os.path.exists(config):
        return os.path.abspath(config)

    raise ValueError("Unable to locate config.  Use --config to specify "
                     "path to octomotron.ini")
