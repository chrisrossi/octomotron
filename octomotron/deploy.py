from octomotron.utils import get_plan


def config_parser(name, subparsers):
    parser = subparsers.add_parser(name, help='Create a new staging instance.')
    parser.add_argument('-B', '--build', default=None,
        help='Which build to use. Optional if only one build is configured.')
    parser.add_argument('-R', '--branch', default=None,
        help='Which branch to check out for main development package. Default '
        'is same as name of staging site.')
    parser.add_argument('-S', '--branches', action='append',
        metavar='pkg_name=branch', help='Specify branches to checkout for '
        'other development packages.')
    parser.add_argument('name', help='Name of site to create.')
    parser.set_defaults(func=main, parser=parser)


def main(args):
    harness = args.harness
    plan = get_plan(args)
    site = harness.new_site(args.name, plan)
    site.realize()
    site.bootstrap()
    branch = args.branch
    if not branch:
        branch = args.name
    if args.branches:
        branches = dict([b.split('=') for b in args.branches])
    else:
        branches = {}
    site.checkout_sources(branch, branches)
    site.buildout()
    site.init_data()
    site.startup()
    site.state = site.RUNNING
    site.save()
    harness.reload_server()
