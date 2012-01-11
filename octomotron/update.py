import logging
from octomotron.utils import only_one

log = logging.getLogger(__name__)


def config_parser(name, subparsers):
    parser = subparsers.add_parser(
        name, help='Update code on all staging instances.')
    parser.set_defaults(func=main, parser=parser)


@only_one('update')
def main(args):
    sites = args.harness.sites
    for site_name in sorted(sites.keys()):
        site = sites[site_name]
        if site.state != site.RUNNING:
            log.warn("Skipping %s (%s)", site_name, site.state)
            continue
        rebuild_required = site.update_sources()
        if not rebuild_required:
            rebuild_required = site.rebuild_required()
        if rebuild_required:
            log.info("Rebuilding %s", site_name)
            site.state = site.UPDATING
            site.save()
            site.pause()
            site.buildout()
            site.refresh_data()
            site.resume()
            site.state = site.RUNNING
            site.save()
        else:
            log.info("%s is up to date", site_name)
