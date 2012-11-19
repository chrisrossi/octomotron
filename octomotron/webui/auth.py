import pam
import pkg_resources

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.security import forget

from .htpasswd import PasswordFile


def config_auth_policy(config):
    settings = config.registry.settings
    name = settings.get('auth_policy', 'promiscuous')
    if '#' in name:
        dist, name = name.split('#')
    else:
        dist = 'octomotron'
    policy = pkg_resources.load_entry_point(
        dist, 'octomotron.auth_policy', name)
    policy(config)


def config_promiscuous_auth_policy(config):
    pass


def config_basic_pam_auth_policy(config):
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_authentication_policy(BasicAuthAuthenticationPolicy(
        pam_authenticate, realm="Octomotron"))
    config.add_view(basic_challenge, context=HTTPForbidden)


def config_basic_local_auth_policy(config):
    settings = config.registry.settings
    htpasswdfile = settings['htpasswd']
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_authentication_policy(BasicAuthAuthenticationPolicy(
        local_authenticate(htpasswdfile), realm="Octomotron"))
    config.add_view(basic_challenge, context=HTTPForbidden)


def pam_authenticate(username, password, request):
    if pam.authenticate(username, password):
        return []
    return None


def local_authenticate(htpasswdfile):
    passwords = PasswordFile(htpasswdfile)
    def check(username, password, request):
        if passwords.check(username, password):
            return []
        return None
    return check


def basic_challenge(context, request):
    response = HTTPUnauthorized()
    response.headers.update(forget(request))
    return response
