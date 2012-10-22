from octomotron.utils import get_harness


def config_parser(name, subparsers):
    parser = subparsers.add_parser(name, help='Approve a site.')
    parser.add_argument('name', help='Name of site to approve.')
    parser.set_defaults(func=main, parser=parser)


def main(args):
    harness = get_harness(args)
    site = harness.sites.get(args.name)
    if not site:
        args.parser.error("No such site: %s" % args.name)
    site.status = site.APPROVED
    site.save()
    harness.reload_server()
