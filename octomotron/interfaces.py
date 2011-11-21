import abc


class AbstractBuild(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self.config = config

    def configure(self, other_config):
        """
        Return a dictionary of configuration values for this particular build.
        other_config is a compilation of all other configuration keys in all
        other builds, since some configuration keys (like port numbers,
        database connection strings, etc...) will have to be unique per build.

        If `http_port` is not included here, it will be added to the build's
        configuration by octomotron, since it is required.
        """
        return {}

    def template_resources(self):
        """
        Return tuple of (package, path) for use by pkg_resources that points
        to the root dir of the buildout template files for this build.
        """
        return self.__class__.__module__, '__build__'

    def init_data(self, site):
        """
        Do whatever you need to do to initialize data for this site, including
        creating databases.
        """

    def startup(self, site):
        """
        Execute whatever command necessary to start http server for hosted
        application listening on configured port.
        """

    def shutdown(self, site):
        """
        Execute whatever command necessary to shutdown http server for hosted
        application.
        """

    def remove_data(self, site):
        """
        Delete the data used by the test instance.
        """

    def rebuild_required(self, site):
        """
        Check if there's some reason, besides git source code changing, which
        is already detected, that redoing the buildout is required.
        """
        return False

    def pause(self, site):
        """
        Do whatever needs to be done to pause the site during an update.
        """

    def resume(self, site):
        """
        Do whatever needs to be done to resume site after an update.
        """

    def refresh_data(self, site):
        """
        Do whatever needs to be done to refresh data during an update.
        """
