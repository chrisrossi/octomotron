from octomotron.utils import get_harness


def config_parser(name, subparsers):
    parser = subparsers.add_parser(name, help='Remove a staging instance.')
    parser.add_argument('name', help='Name of site to remove.')
    parser.set_defaults(func=main, parser=parser)


def main(args):
    harness = get_harness(args)
    site = harness.sites.get(args.name)
    if not site:
        args.parser.error("No such site: %s" % args.name)
    try:
        site.shutdown()
        site.remove_data()
        site.delete()
    except:
        site.status = site.REMOVAL_FAILED
        site.save()
        raise
    finally:
        harness.reload_server()
