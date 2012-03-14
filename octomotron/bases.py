import abc
import os
import pkg_resources

from octomotron.utils import shell


class AbstractBuild(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, site):
        self.site = site

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

    def setup(self):
        """
        Perform setup needed for your application, eg run bootstrap your build,
        run pip install, etc...
        """

    def refesh(self):
        """
        Perform any steps need after updating code.
        """

    def init_data(self):
        """
        Do whatever you need to do to initialize data for this site, including
        creating databases.
        """

    def startup(self):
        """
        Execute whatever command necessary to start http server for hosted
        application listening on configured port.
        """

    def shutdown(self):
        """
        Execute whatever command necessary to shutdown http server for hosted
        application.
        """

    def remove_data(self):
        """
        Delete the data used by the test instance.
        """

    def rebuild_required(self):
        """
        Check if there's some reason, besides git source code changing, which
        is already detected, that redoing the buildout is required.
        """
        return False

    def pause(self):
        """
        Do whatever needs to be done to pause the site during an update.
        """

    def resume(self):
        """
        Do whatever needs to be done to resume site after an update.
        """

    def refresh_data(self):
        """
        Do whatever needs to be done to refresh data during an update.
        """

    def pages(self):
        """
        Provide a list of site-relative urls to pages in the site that should
        be linked to from the Octomotron web UI.
        """
        return [{'href': '/', 'title': 'home'}]


class VirtualenvBuild(AbstractBuild):

    def setup(self):
        site = self.site
        os.chdir(site.build_dir)
        shell('virtualenv -p %s --no-site-packages .' % site.harness.python)
        if os.path.exists('requirements.txt'):
            shell('bin/pip install -r requirements.txt')
        src = os.path.abspath('src')
        for dirname in os.listdir(src):
            srcdir = os.path.join(src, dirname)
            setup_py = os.path.join(srcdir, 'setup.py')
            if os.path.exists(setup_py):
                os.chdir(srcdir)
                shell('../../bin/python setup.py develop')


class BuildoutBuild(AbstractBuild):

    def setup(self):
        site = self.site
        os.chdir(site.build_dir)
        shell('virtualenv -p %s --no-site-packages .' % site.harness.python)
        shell('bin/python bootstrap.py')

        buildout_ext = pkg_resources.resource_filename(
            'octomotron', 'buildout_ext')
        os.chdir(buildout_ext)
        python = os.path.join(site.build_dir, 'bin', 'python')
        shell('%s setup.py develop' % python)
        shell('bin/buildout')

    def refresh(self):
        site = self.site
        os.chdir(site.build_dir)
        shell('bin/buildout')
