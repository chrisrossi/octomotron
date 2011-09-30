

def config_parser(name, subparsers):
    parser = subparsers.add_parser(
        name, help='Update code on all staging instances.')
    parser.set_defaults(func=main, parser=parser)


def main(args):
    sites = args.harness.sites
    for site_name in sorted(sites.keys()):
        site = sites[site_name]
        rebuild_required = site.update_sources()
        if not rebuild_required:
            rebuild_required = site.rebuild_required()
        if rebuild_required:
            print "Rebuilding %s" % site_name
            site.pause()
            site.buildout()
            site.refresh_data()
            site.resume()
        else:
            print "%s is up to date" % site_name


