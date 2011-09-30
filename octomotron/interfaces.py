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
        Return package, path for use by distutils' pkg_resources that points to
        the root dir of the buildout template files for this build.
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