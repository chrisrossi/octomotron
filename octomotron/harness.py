import ConfigParser
import json
import logging
import os
import pkg_resources
import shutil
import sys

from octomotron.exc import UserError
from octomotron.utils import shell
from octomotron.utils import shell_capture
from octomotron.utils import unique_int

OCTOMOTRON_CFG = '.octomotron.cfg'


log = logging.getLogger(__name__)


class Harness(object):

    def __init__(self, ini_path):
        self.ini_path = ini_path
        here = os.path.dirname(os.path.abspath(ini_path))
        parser = ConfigParser.ConfigParser({'here' :here})
        parser.read(ini_path)
        config = dict(parser.items('DEFAULT'))
        config.update(parser.items('build'))

        # Populate sources
        section = config.pop('sources', 'sources')
        self.sources = sources = []
        self.always_checkout = config.pop('always_checkout', '').split()
        for name, source in parser.items(section):
            if name == 'here':
                continue
            parts = source.split()
            if len(parts) == 1:
                url, branch = source, 'master'
            elif len(parts) == 2:
                url, branch = parts
            else:
                raise UserError('Bad sources line: %s' % source)
            sources.append({'name': name, 'url': url, 'branch': branch})

        first = sources[0]['name']
        if first not in self.always_checkout:
            self.always_checkout.append(first)

        bin = os.path.abspath(sys.argv[0])
        env = os.path.dirname(os.path.dirname(bin))
        self.builds_dir = config.pop('builds_dir', os.path.join(env, 'builds'))
        self.var = config.pop('var', os.path.join(env, 'var'))
        self.pids = config.pop('pids', os.path.join(self.var, 'pids'))
        self.python = config.pop('python', 'python')
        self.sources_dir = config.pop('sources_dir', 'src')
        self.build = config.pop('use')
        self.config = config

        if not os.path.exists(self.builds_dir):
            os.makedirs(self.builds_dir)

        self.sites = sites = {}
        for name in os.listdir(self.builds_dir):
            if name.startswith('.'):
                continue
            sites[name] = Site.load(self, os.path.join(self.builds_dir, name))

    def new_site(self, name):
        path = os.path.join(self.builds_dir, name)
        if os.path.exists(path):
            raise UserError("Site already exists: %s" % name)
        return Site(self, name, self.sites.values())

    def reload_server(self):
        os.utime(self.ini_path, None)


class Site(object):

    BUILDING = 'building'
    UPDATING = 'updating'
    RUNNING = 'running'

    @classmethod
    def load(cls, harness, path):
        serial_file = os.path.join(path, OCTOMOTRON_CFG)
        with open(serial_file) as fp:
            serial = json.load(fp)
        site = cls.__new__(cls)
        site.harness = harness
        site.name = serial['name']
        site.config = serial['config']
        site.state = serial['state']
        site.build_dir = path
        site._init_common()
        return site

    def __init__(self, harness, name, other_sites):
        self.harness = harness
        self.name = name
        self._init_common()
        self.config = self._configure(other_sites)
        self.build_dir = os.path.join(self.harness.builds_dir, self.name)
        self.state = self.BUILDING
        self.save()

    def _configure(self, other_sites):
        other_config = {}
        for site in other_sites:
            for name, value in site.config.items():
                other_config.setdefault(name, []).append(value)
        config = self.build.configure(other_config)
        if 'http_port' not in config:
            config['http_port'] = unique_int(
                8001, other_config.get('http_port'))
        return config

    def _init_common(self):
        ep_dist, ep_name = self.harness.build.split('#')
        self.build = pkg_resources.load_entry_point(
            ep_dist, 'octomotron.build', ep_name)(self)

    def save(self):
        build_dir = self.build_dir
        serial = {'config': self.config,
                  'state': self.state, 'name': self.name}
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)
        serial_file = os.path.join(build_dir, OCTOMOTRON_CFG)
        with open(serial_file, 'w') as fp:
            json.dump(serial, fp, indent=4)

    def realize(self):
        build_dir = self.build_dir
        config = self.config
        package, path = self.build.template_resources()

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

    def checkout_sources(self, branch, other_branches):
        src = os.path.join(self.build_dir, self.harness.sources_dir)
        if not os.path.exists(src):
            os.mkdir(src)
        for source in self.harness.sources:
            name = source['name']
            default = 'master' if name in self.harness.always_checkout else None
            branch = other_branches.get(name, default)
            if branch is None:
                continue
            source['branch'] = branch
            source_dir = os.path.join(src, name)
            if os.path.exists(source_dir):
                continue

            # Use cache, so most objects can be copied locally in most cases
            cachedir = os.path.join(self.harness.var, 'gitcache')
            url = source['url']
            branch = source['branch']
            if not os.path.exists(cachedir):
                os.mkdir(cachedir)
            cacherepo = os.path.join(cachedir, name) + '.git'
            if not os.path.exists(cacherepo):
                os.chdir(cachedir)
                shell('git clone --mirror %s %s.git' % (url, name))
            else:
                os.chdir(cacherepo)
                shell('git fetch')

            os.chdir(src)
            shell('git clone --branch %s %s' % (branch, cacherepo))
            shell('git remote rm origin')
            shell('git remote add origin %s' % url)
            shell('git config branch.%s.remote origin' % branch)
            shell('git config branch.%s.merge refs/heads/%s' % (
                branch, branch))

    def setup(self):
        self.build.setup()

    def refresh(self):
        self.build.refresh()

    def init_data(self):
        self.build.init_data()

    def startup(self):
        self.build.startup()

    def shutdown(self):
        self.build.shutdown()

    def remove_data(self):
        self.build.remove_data()

    def delete(self):
        shutil.rmtree(self.build_dir)

    def update_sources(self):
        all_merged = self.name != 'master'
        rebuild_required = False
        sources = os.path.join(self.build_dir, self.harness.sources_dir)
        for dirname in os.listdir(sources):
            if dirname.startswith('.'):
                continue
            src = os.path.join(sources, dirname)
            os.chdir(src)
            output = shell_capture('git pull')
            rebuild_required = (rebuild_required or
                                'Already up-to-date' not in output)
            log.info(output)
            if all_merged:
                merged = False
                output = shell_capture('git branch --merged origin/master')
                for line in output.split('\n'):
                    if line.startswith('*'):
                        merged = True
                        break
                all_merged = merged

        return rebuild_required, all_merged

    def rebuild_required(self):
        return self.build.rebuild_required()

    def pause(self):
        self.build.pause()

    def resume(self):
        self.build.resume()

    def refresh_data(self):
        self.build.refresh_data()

    def pages(self):
        return self.build.pages()
