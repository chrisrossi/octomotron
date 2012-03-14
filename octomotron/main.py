import argparse
import logging
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
    try:
        args.func(args)
    except UserError, e:
        args.parser.error(str(e))



