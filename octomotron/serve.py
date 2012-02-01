import os
import sys

from paste.proxy import Proxy
from paste.script.serve import ServeCommand

from webob.exc import HTTPNotFound
from webob.request import Request
from webob.response import Response

from octomotron.harness import Harness
from octomotron.webui import WebUI


class Application(object):

    def __init__(self, ini_path):
        self.ini_path = ini_path
        self.load()

    def load(self):
        ini_path = self.ini_path
        self.mtime = os.path.getmtime(ini_path)
        self.harness = Harness(ini_path)
        self.webui = WebUI(self.harness)
        self.proxies = {}

    def __call__(self, environ, start_response):
        if os.path.getmtime(self.ini_path) != self.mtime:
            self.load()

        response = self.webui(Request(environ))
        if response is not None:
            return response(environ, start_response)

        environ = environ.copy()
        if environ['SCRIPT_NAME'] == '/':
            environ['SCRIPT_NAME'] = ''
        path = environ['PATH_INFO'].lstrip('/')
        path = path.split('/')
        site_name = path.pop(0)
        environ['PATH_INFO'] = '/' + '/'.join(path)

        proxies = self.proxies
        proxy = proxies.get(site_name)
        if not proxy:
            site = self.harness.sites.get(site_name)
            if not site:
                return HTTPNotFound()(environ, start_response)
            url = 'http://localhost:%d/' % site.config['http_port']
            proxies[site_name] = proxy = Proxy(url)

        # XXX This kludge assumes the hosted application is using repoze.vhm.
        #     A better solution would be if the proxy could be configured to
        #     to send the correct Host header to the downstream application.
        #     Will require forking paste.proxy and maintaining elsewhere,
        #     something someone should probably do anyway.
        scheme = environ['wsgi.url_scheme']
        vhm_host = '%s://%s/%s' % (scheme, environ['HTTP_HOST'], site_name)
        environ['HTTP_X_VHM_HOST'] = vhm_host
        return proxy(environ, start_response)

    def index_page(self, request):
        html = ["<html><head><title>Octomotron!</title></head>\n",
                "<body>\n",
                "  <h1>Sites</h1>\n",
                "  <ul>\n"]
        for site in sorted(self.harness.sites.keys()):
            html.append('    <li><a href="%s">%s</a></li>\n' %
                        (request.url + site, site))
        html.append("  </ul>\n</body>\n</html>")
        html = ''.join(html)
        return Response(html, content_type='text/html')


def make_app(global_config, ini_path):
    return Application(ini_path)


def config_parser(name, subparsers):
    parser = subparsers.add_parser(
        name, help='Serve the Octomotron application.')
    parser.set_defaults(func=serve, parser=parser)


def serve(args):
    os.environ['PASTE_CONFIG_FILE'] = args.config

    cmd = ServeCommand('jove serve')
    exit_code = cmd.run([])
    sys.exit(exit_code)
