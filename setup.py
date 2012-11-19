import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
except IOError:
    README = CHANGES = ''

install_requires=[
    'cryptacular',
    'pam',
    'Paste',
    'PasteScript',
    'pyramid',
    'WebOb',
    ]

if sys.version < '2.7':
    install_requires.append('argparse')

tests_require = install_requires + ['mock']
if sys.version < '2.7':
    tests_require.append('unittest2')

testing_extras = tests_require + ['nose', 'coverage']

setup(name='octomotron',
      version='0.2dev',
      description=('A tool for rapid deployment of multiple evluation copies '
                   'of a web application based on different git branches.'),
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "License :: Repoze Public License",
        ],
      keywords='web wsgi pylons',
      author="Chris Rossi",
      author_email="pylons-devel@googlegroups.com",
      url="http://pylonsproject.org",
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires = install_requires,
      tests_require = tests_require,
      test_suite="octomotron.tests",
      extras_require={
          'testing': testing_extras},
      entry_points = """\
      [paste.app_factory]
      main = octomotron.webui.application:Application

      [console_scripts]
      octomotron = octomotron.main:main

      [octomotron.script]
      adduser = octomotron.webui.htpasswd:config_parser
      approve = octomotron.approve:config_parser
      remove = octomotron.remove:config_parser
      rm = octomotron.remove:config_parser
      serve = octomotron.serve:config_parser
      deploy = octomotron.deploy:config_parser
      update = octomotron.update:config_parser
      example = octomotron.example:config_parser

      [octomotron.auth_policy]
      promiscuous = octomotron.webui.auth:config_promiscuous_auth_policy
      basic_pam = octomotron.webui.auth:config_basic_pam_auth_policy
      basic_local = octomotron.webui.auth:config_basic_local_auth_policy
      """
      )
