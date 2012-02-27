import logging
from octomotron.remove import main as remove
from octomotron.utils import only_one

log = logging.getLogger(__name__)


def config_parser(name, subparsers):
    parser = subparsers.add_parser(
        name, help='Update code on all staging instances.')
    parser.set_defaults(func=main, parser=parser)


@only_one('update')
def main(args):
    harness = args.harness
    sites = harness.sites
    for site_name in sorted(sites.keys()):
        site = sites[site_name]
        if site.state != site.RUNNING:
            log.warn("Skipping %s (%s)", site_name, site.state)
            continue
        rebuild_required, merged = site.update_sources()
        if merged:
            log.info("%s merged.  Removing...", site_name)
            args.name = site_name
            return remove(args)

        if not rebuild_required:
            rebuild_required = site.rebuild_required()
        if rebuild_required:
            log.info("Rebuilding %s", site_name)
            site.state = site.UPDATING
            site.save()
            harness.reload_server()
            site.pause()
            site.buildout()
            site.refresh_data()
            site.resume()
            site.state = site.RUNNING
            site.save()
            harness.reload_server()
        else:
            log.info("%s is up to date", site_name)
