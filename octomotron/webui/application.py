from paste.proxy import Proxy

from pyramid.config import Configurator
from pyramid.exceptions import NotFound
from pyramid.request import Request
from pyramid.view import view_config

from octomotron.harness import Harness


def main(global_config, **config):
    settings = global_config.copy()
    settings.update(config)
    ini_path = settings.pop('ini_path')

    config = Configurator(settings=settings, root_factory=Octomotron)
    registry = config.registry
    registry['harness'] = Harness(ini_path)
    registry['proxies'] = {}
    config.add_static_view('/OCTOSTATIC', 'static')
    config.scan()

    return config.make_wsgi_app()


class Octomotron(object):
    __parent__ = __name__ = None

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
        return type(self)(self.site, self.path + [name])


@view_config(context=Site)
def proxy(context, request):
    site = context.site
    if site.state != 'running':
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


@view_config(context=Octomotron)
def home(request):
    return request.invoke_subrequest(
        Request.blank(request.static_url('static/octomotron.html')))


@view_config(context=AdminUI, name='get_sites', renderer='json')
def get_sites(request):
    sites = []
    for site in request.registry['harness'].sites.values():
        if site.state == 'running':
            pages = [{'href': '/%s%s' % (site.name, page['href']),
                      'title': page['title']} for page in site.pages()]
        else:
            pages = []
        sites.append({'title': site.name, 'status': site.state,
                      'pages': pages})

    return {'sites': sites}
