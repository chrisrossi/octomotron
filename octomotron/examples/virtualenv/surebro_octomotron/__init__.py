import logging
import os
import time

from octomotron.bases import VirtualenvBuild
from octomotron.utils import shell
from octomotron.utils import unique_int

log = logging.getLogger(__name__)


class Build(VirtualenvBuild):

    def configure(self, other_config):
        return {
            'supervisord_port': unique_int(
                7000, other_config.get('supervisord_port')),
            'zeo_port': unique_int(
                7500, other_config.get('zeo_port')),
        }

    def startup(self):
        os.chdir(self.site.build_dir)
        shell('bin/supervisord')

    def shutdown(self):
        os.chdir(self.site.build_dir)
        shell('bin/supervisorctl shutdown', False)
        pidfile = 'var/supervisord.pid'
        while os.path.exists(pidfile):
            # If we have a proc filesystem, we can make sure it isn't a stale
            # pid file
            if os.path.exists('/proc'):
                pid = open(pidfile).read().strip()
                procpid = '/proc/%s' % pid
                if not os.path.exists(procpid):
                    log.warn("Removing stale supervisord.pid")
                    os.remove(pidfile)
                    break

            log.info("Waiting for supervisor to shutdown...")
            time.sleep(1)

    pause = shutdown
    resume = startup
