from octomotron.utils import get_harness


def config_parser(name, subparsers):
    parser = subparsers.add_parser(name, help='Create a new staging instance.')
    parser.add_argument('-R', '--branch', default=None,
        help='Which branch to check out for main development package. Default '
        'is same as name of staging site.')
    parser.add_argument('-S', '--branches', action='append',
        metavar='pkg_name=branch', help='Specify branches to checkout for '
        'other development packages.')
    parser.add_argument('name', help='Name of site to create.')
    parser.set_defaults(func=main, parser=parser)


def main(args):
    branch = args.branch
    if not branch:
        branch = args.name
    if args.branches:
        branches = dict([b.split('=') for b in args.branches])
    else:
        branches = {}

    harness = get_harness(args)
    site = harness.new_site(args.name)
    harness.reload_server()
    site.realize()
    site.checkout_sources(branch, branches)
    site.setup()
    site.init_data()
    site.startup()
    site.run_state = site.RUNNING
    site.save()
    harness.reload_server()
