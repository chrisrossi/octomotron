from paste.proxy import Proxy

from pyramid.config import Configurator
from pyramid.exceptions import NotFound
from pyramid.request import Request
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.security import Authenticated
from pyramid.view import view_config

from octomotron.webui.auth import config_auth_policy
from octomotron.harness import Harness


VIEW = 'view'


class Application(object):

    def __init__(self, global_config, **config):
        self.settings = global_config.copy()
        self.settings.update(config)
        self.ini_path = self.settings.pop('ini_path')
        self.harness = Harness(self.ini_path)
        self.pyramid_app = self.make_pyramid_app(self.harness)

    def make_pyramid_app(self, harness):
        config = Configurator(settings=self.settings, root_factory=Octomotron)
        registry = config.registry
        registry['harness'] = harness
        registry['proxies'] = {}
        config.add_static_view('/OCTOSTATIC', 'static')
        config_auth_policy(config)
        config.scan()

        return config.make_wsgi_app()

    def __call__(self, environ, start_response):
        if self.harness.out_of_date():
            self.harness = Harness(self.ini_path)
            self.pyramid_app = self.make_pyramid_app(self.harness)
        request = Request(environ)
        path = filter(None, request.path_info.split('/'))
        name = path[0] if path else None
        site = self.harness.sites.get(name)
        if site:
            request.registry = self.pyramid_app.registry
            site = Site(site)
            site.path = path[1:]
            return request.get_response(proxy(site, request))(
                environ, start_response)
        return self.pyramid_app(environ, start_response)


class Octomotron(object):
    __parent__ = __name__ = None
    __acl__ = [(Allow, Authenticated, (VIEW,)), DENY_ALL]

    def __init__(self, request):
        self.harness = request.registry['harness']

    def __getitem__(self, name):
        if name == 'OCTOMOTRON':
            child = AdminUI()
        else:
            child = Site(self.harness.sites[name])
        child.__name__ = name
        child.__parent__ = self
        return child


class AdminUI(object):
    """
    Resource for Octomotron web UI.
    """


class Site(object):
    """
    Resource for traversing into one of the deployed branches.
    """
    def __init__(self, site, path=[]):
        self.site = site
        self.path = path

    def __getitem__(self, name):
        child = type(self)(self.site, self.path + [name])
        child.__name__ = name
        child.__parent__ = self
        return child


def timeit(f):
    import time
    def wrapper(context, request):
        start = time.time()
        try:
            return f(context, request)
        finally:
            print "Elapsed: %0.3f" % (time.time() - start)

    return wrapper


@view_config(context=Site, permission=VIEW)
@timeit
def proxy(context, request):
    site = context.site
    if site.run_state != 'running':
        raise NotFound

    subrequest = request.copy()
    if request.script_name == '/':
        subrequest.script_name == ''

    # XXX: Get this from untraversed path instead
    subrequest.path_info = '/' + '/'.join(context.path)

    proxies = request.registry['proxies']
    proxy = proxies.get(site.name)
    if not proxy:
        url = 'http://localhost:%d/' % site.config['http_port']
        proxies[site.name] = proxy = Proxy(url)

    # XXX This kludge assumes the hosted application is using repoze.vhm.
    #     A better solution would be if the proxy could be configured to
    #     to send the correct Host header to the downstream application.
    #     Will require forking paste.proxy and maintaining elsewhere,
    #     something someone should probably do anyway.
    vhm_host = '%s://%s/%s' % (request.scheme, request.host, site.name)
    subrequest.headers['X-Vhm-Host'] = vhm_host
    return subrequest.get_response(proxy)


@view_config(context=Octomotron, permission=VIEW)
def home(request):
    return request.invoke_subrequest(
        Request.blank(request.static_url('static/octomotron.html')))


@view_config(context=AdminUI, name='get_sites', renderer='json',
             permission=VIEW)
def get_sites(request):
    sites = []
    for site in request.registry['harness'].sites.values():
        if site.run_state == 'running':
            pages = [{'href': '/%s%s' % (site.name, page['href']),
                      'title': page['title']} for page in site.pages()]
        else:
            pages = []
        sites.append({'title': site.name, 'run_state': site.run_state,
                      'status': site.status, 'pages': pages})

    return {'sites': sites}
