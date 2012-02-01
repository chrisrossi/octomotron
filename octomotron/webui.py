import json
import os
import pkg_resources

from webob.response import Response


class WebUI(object):

    def __init__(self, harness):
        self.harness = harness

    def __call__(self, request):
        path = request.path_info.strip('/')

        # Main page
        if path == '':
            return static_file('octomotron.html')

        # All other API is under /OCTOMOTRON, to try to avoid name collisions
        # with hosted sites.
        if not path.startswith('OCTOMOTRON/'):
            return None
        path = path[11:]  # len('OCTOMOTRON/') == 11

        # Might be an api call
        method = getattr(self, path, None)
        if method is not None:
            return method(request)

        # Might be a static file
        response = static_file(path)
        if response is not None:
            return response

    def get_sites(self, request):
        return JSONResponse({'sites': [
            {'title': site.name,
             'status': site.state,
             'pages': [
                 {'href': '/%s%s' % (site.name, page['href']),
                  'title': page['title']} for page in site.pages()]
            } for site in self.harness.sites.values()]})


class JSONResponse(Response):

    def __init__(self, data):
        super(JSONResponse, self).__init__(
            body=json.dumps(data),
            content_type="application/json",
        )


exts = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript'}


def static_file(fname):
    path = 'static/%s'  % fname
    if not pkg_resources.resource_exists('octomotron', path):
        return None
    ext = os.path.splitext(fname)[1]
    mimetype = exts[ext]
    response = Response(
        app_iter=pkg_resources.resource_stream('octomotron', path),
        content_type=mimetype)
    return response
