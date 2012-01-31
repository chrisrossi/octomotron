

def config_parser(name, subparsers):
    parser = subparsers.add_parser(name, help='Remove a staging instance.')
    parser.add_argument('name', help='Name of site to remove.')
    parser.set_defaults(func=main, parser=parser)


def main(args):
    harness = args.harness
    site = harness.sites.get(args.name)
    if not site:
        args.parser.error("No such site: %s" % site)
    site.shutdown()
    site.remove_data()
    site.delete()
    harness.reload_server()
