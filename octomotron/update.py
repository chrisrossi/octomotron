import logging
from octomotron.remove import main as remove
from octomotron.utils import get_harness
from octomotron.utils import only_one

log = logging.getLogger(__name__)


def config_parser(name, subparsers):
    parser = subparsers.add_parser(
        name, help='Update code on all staging instances.')
    parser.set_defaults(func=main, parser=parser)


@only_one('update')
def main(args):
    harness = get_harness(args)
    sites = harness.sites
    for site_name in sorted(sites.keys()):
        site = sites[site_name]
        if site.run_state != site.RUNNING:
            log.warn("Skipping %s (%s)", site_name, site.run_state)
            continue
        rebuild_required, merged = site.update_sources()
        if merged:
            log.info("%s merged.  Removing...", site_name)
            args.name = site_name
            remove(args)
            continue

        if not rebuild_required:
            rebuild_required = site.rebuild_required()
        if rebuild_required:
            log.info("Rebuilding %s", site_name)
            site.run_state = site.UPDATING
            site.save()
            harness.reload_server()
            site.pause()
            site.refresh()
            site.refresh_data()
            site.resume()
            site.run_state = site.RUNNING
            site.save()
            harness.reload_server()
        else:
            log.info("%s is up to date", site_name)
