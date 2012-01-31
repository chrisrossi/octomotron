import ConfigParser
import os
import pkg_resources
import json
import shutil
import sys

from octomotron.exc import UserError
from octomotron.utils import shell
from octomotron.utils import shell_capture
from octomotron.utils import unique_int

OCTOMOTRON_CFG = '.octomotron.cfg'


class Harness(object):

    def __init__(self, path):
        parser = ConfigParser.ConfigParser()
        parser.read(path)
        defaults = dict(parser.items('DEFAULT'))
        self.plans = plans = {}
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
            plans[name] = BuildPlan(parser, self, name, config)

        bin = os.path.abspath(sys.argv[0])
        env = os.path.dirname(os.path.dirname(bin))
        if 'builds_dir' not in octomotron:
            octomotron['builds_dir'] = os.path.join(env, 'builds')
        if 'var' not in octomotron:
            octomotron['var'] = os.path.join(env, 'var')
        if 'pids' not in octomotron:
            octomotron['pids'] = os.path.join(octomotron['var'], 'pids')

        self.__dict__.update(octomotron)

        if not os.path.exists(self.builds_dir):
            os.makedirs(self.builds_dir)

        self.sites = sites = {}
        for name in os.listdir(self.builds_dir):
            if name.startswith('.'):
                continue
            sites[name] = Site.load(self, os.path.join(self.builds_dir, name))

    def new_site(self, name, plan):
        path = os.path.join(self.builds_dir, name)
        if os.path.exists(path):
            raise UserError("Site already exists: %s" % name)
        return Site(self, name, plan, self.sites.values())


class BuildPlan(object):

    def __init__(self, parser, harness, name, config):
        self.harness = harness
        self.name = name

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
        self.config = config


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
        site.plan = harness.plans[serial['plan']]
        site.config = serial['config']
        site.state = serial['state']
        site.build_dir = path
        site._init_common()
        return site

    def __init__(self, harness, name, plan, other_sites):
        self.harness = harness
        self.name = name
        self.plan = plan
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
        ep_dist, ep_name = self.plan.config['use'].split('#')
        self.build = pkg_resources.load_entry_point(
            ep_dist, 'octomotron.build', ep_name)(self)

    def save(self):
        build_dir = self.build_dir
        serial = {'plan': self.plan.name, 'config': self.config,
                  'state': self.state}
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

    def bootstrap(self):
        os.chdir(self.build_dir)
        shell('virtualenv -p %s --no-site-packages .' % self.plan.python)
        shell('bin/python bootstrap.py')

    def checkout_sources(self, branch, other_branches):
        src = os.path.join(self.build_dir, self.plan.sources_dir)
        if not os.path.exists(src):
            os.mkdir(src)
        os.chdir(src)
        sources = list(self.plan.sources)
        sources[0]['branch'] = branch
        checkout = [sources.pop(0)]
        for source in sources:
            name = source['name']
            branch = other_branches.get(name, None)
            if branch is None:
                continue
            source['branch'] = branch
            source_dir = os.path.join(src, name)
            if os.path.exists(source_dir):
                continue
            checkout.append(source)

        for source in checkout:
            shell('git clone --branch %s %s' % (
                source['branch'], source['url']))

    def buildout(self):
        buildout_ext = pkg_resources.resource_filename(
            'octomotron', 'buildout_ext')
        os.chdir(buildout_ext)
        python = os.path.join(self.build_dir, 'bin', 'python')
        shell('%s setup.py develop' % python)
        os.chdir(self.build_dir)
        shell('bin/buildout')

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
        rebuild_required = False
        sources = os.path.join(self.build_dir, self.plan.sources_dir)
        for dirname in os.listdir(sources):
            if dirname.startswith('.'):
                continue
            src = os.path.join(sources, dirname)
            os.chdir(src)
            output = shell_capture('git pull')
            rebuild_required = (rebuild_required or
                                'Already up-to-date' not in output)
            print output
        return rebuild_required

    def rebuild_required(self):
        return self.build.rebuild_required()

    def pause(self):
        self.build.pause()

    def resume(self):
        self.build.resume()

    def refresh_data(self):
        self.build.refresh_data()
