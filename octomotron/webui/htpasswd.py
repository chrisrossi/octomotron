"""
Not really compatible with other htpassword providers.  Uses bcrypt.
"""
import getpass
import os
from cryptacular.bcrypt import BCRYPTPasswordManager
from octomotron.utils import get_harness


class PasswordFile(object):
    bcrypt = BCRYPTPasswordManager()

    def __init__(self, filename):
        self.filename = filename
        self.timestamp = 0
        self._passwords = {}

    def _get_passwords(self):
        if os.path.exists(self.filename):
            mtime = os.path.getmtime(self.filename)
            if mtime > self.timestamp:
                self._passwords = dict([
                    line.strip().split(':') for line in open(self.filename)])
        return self._passwords

    def set_password(self, name, password):
        passwords = self._get_passwords()
        passwords[name] = self.bcrypt.encode(password)

    def save(self):
        with open(self.filename, 'w') as f:
            for credential in self._passwords.items():
                print >> f, '%s:%s' % credential

    def check(self, name, password):
        passwords = self._get_passwords()
        hashed = passwords.get(name)
        return hashed and self.bcrypt.check(hashed, password)


def config_parser(name, subparsers):
    parser = subparsers.add_parser(
        name, help='Manage user passwords for local auth.')
    parser.set_defaults(func=adduser, parser=parser)


def adduser(args):
    harness = get_harness(args)
    htpasswdfile = harness.config['htpasswd']
    passwords = PasswordFile(htpasswdfile)
    username = raw_input('username: ')
    while True:
        password1 = getpass.getpass('password: ')
        password2 = getpass.getpass('verify password: ')
        if password1 == password2:
            break
    passwords.set_password(username, password1)
    passwords.save()

