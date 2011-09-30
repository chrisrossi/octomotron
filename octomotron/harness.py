import ConfigParser
import os
import pkg_resources
import json
import shutil
import sys

from octomotron.exc import UserError
from octomotron.utils import shell
from octomotron.utils import unique_int

OCTOMOTRON_CFG = '.octomotron.cfg'


class Harness(object):

    def __init__(self, path):
        parser = ConfigParser.ConfigParser()
        parser.read(path)
        defaults = dict(parser.items('DEFAULT'))
        self.builds = builds = {}
        octomotron = defaults.copy()
        for section in parser.sections():
            if section == 'octomotron':
                octomotron.update(parser.items(section))
                continue
            elif not section.startswith('build:'):
                continue
            name = section[6:].strip()
            config = defaults.copy()
            config.update(parser.items(section))
            builds[name] = Build(parser, self, name, config)

        if 'builds_dir' not in octomotron:
            bin = os.path.abspath(sys.argv[0])
            env = os.path.dirname(os.path.dirname(bin))
            octomotron['builds_dir'] = os.path.join(env, 'builds')

        self.__dict__.update(octomotron)

        if not os.path.exists(self.builds_dir):
            os.makedirs(self.builds_dir)

        self.sites = sites = {}
        for name in os.listdir(self.builds_dir):
            if name.startswith('.'):
                continue
            sites[name] = Site.load(self, os.path.join(self.builds_dir, name))

    def new_site(self, name, build):
        path = os.path.join(self.builds_dir, name)
        if os.path.exists(path):
            raise UserError("Site already exists: %s" % name)

        config = build.configure(self.sites.values())
        return Site(self, name, build, config)


class Site(object):

    @classmethod
    def load(cls, harness, path):
        serial_file = os.path.join(path, OCTOMOTRON_CFG)
        with open(serial_file) as fp:
            serial = json.load(fp)
        site = cls.__new__(cls)
        site.harness = harness
        site.build = harness.builds[serial['build']]
        site.config = serial['config']
        site.build_dir = path
        return site

    def __init__(self, harness, name, build, config):
        self.harness = harness
        self.name = name
        self.build = build
        self.config = config
        self.build_dir = os.path.join(self.harness.builds_dir, self.name)
        self.save()

    def save(self):
        build_dir = self.build_dir
        serial = {'build': self.build.name, 'config': self.config}
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)
        serial_file = os.path.join(build_dir, OCTOMOTRON_CFG)
        with open(serial_file, 'w') as fp:
            json.dump(serial, fp, indent=4)

    def realize(self):
        self.build.realize(self.build_dir, self.config)

    def bootstrap(self):
        os.chdir(self.build_dir)
        shell('virtualenv -p %s --no-site-packages .' % self.build.python)
        shell('bin/python bootstrap.py')

    def checkout_sources(self, branch, other_branches):
        src = os.path.join(self.build_dir, self.build.sources_dir)
        if not os.path.exists(src):
            os.mkdir(src)
        os.chdir(src)
        sources = list(self.build.sources)
        sources[0]['branch'] = branch
        for source in sources:
            name = source['name']
            source_dir = os.path.join(src, name)
            if os.path.exists(source_dir):
                continue
            branch = other_branches.get(name, source['branch'])
            shell('git clone --branch %s %s' % (branch, source['url']))

    def buildout(self):
        os.chdir(self.build_dir)
        shell('bin/buildout')

    def init_data(self):
        self.build.init_data(self)

    def startup(self):
        self.build.startup(self)

    def shutdown(self):
        self.build.shutdown(self)

    def remove_data(self):
        self.build.remove_data(self)

    def delete(self):
        shutil.rmtree(self.build_dir)


class Build(object):

    def __init__(self, parser, harness, name, config):
        self.harness = harness
        self.name = name
        ep_dist, ep_name = config.pop('use').split('#')
        self._build = pkg_resources.load_entry_point(
            ep_dist, 'octomotron.build', ep_name)(config)

        section = config.pop('sources', 'sources')
        self.sources = sources = []
        for name, source in parser.items(section):
            parts = source.split()
            if len(parts) == 1:
                url, branch = source, 'master'
            elif len(parts) == 2:
                url, branch = parts
            else:
                raise UserError('Bad sources line: %s' % source)
            sources.append({'name': name, 'url': url, 'branch': branch})

        self.python = config.pop('python', 'python')
        self.sources_dir = config.pop('sources_dir', 'src')

    def configure(self, other_sites):
        other_config = {}
        for site in other_sites:
            for name, value in site.config.items():
                other_config.setdefault(name, []).append(value)
        config = self._build.configure(other_config)
        if 'http_port' not in config:
            config['http_port'] = unique_int(
                8001, other_config.get('http_port'))
        return config

    def realize(self, build_dir, config):
        package, path = self._build.template_resources()

        def visit(src, dst):
            if pkg_resources.resource_isdir(package, src):
                if not os.path.exists(dst):
                    os.mkdir(dst)
                for fname in pkg_resources.resource_listdir(package, src):
                    visit(os.path.join(src, fname), os.path.join(dst, fname))
            else:
                is_template = src.endswith('.tmpl')
                if is_template:
                    dst = dst[:-5]
                src_fspath = pkg_resources.resource_filename(package, src)
                with open(src_fspath) as src_fp:
                    with open(dst, 'wb') as dst_fp:
                        realized = src_fp.read()
                        try:
                            if is_template:
                                realized = realized % config
                        except Exception, e:
                            raise UserError("Unable to realize %s: %s" %
                                            (src, str(e)))
                        dst_fp.write(realized)

        visit(path, build_dir)

    def init_data(self, site):
        self._build.init_data(site)

    def startup(self, site):
        self._build.startup(site)

    def shutdown(self, site):
        self._build.shutdown(site)

    def remove_data(self, site):
        self._build.remove_data(site)
