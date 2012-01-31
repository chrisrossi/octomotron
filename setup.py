import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
except IOError:
    README = CHANGES = ''

install_requires=[
    'argparse',
    'Paste',
    'PasteDeploy',
    'PasteScript',
    'WebOb',
    ]

tests_require= install_requires

setup(name='octomotron',
      version='0.1',
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
      entry_points = """\
      [paste.app_factory]
      main = octomotron.serve:make_app

      [console_scripts]
      octomotron = octomotron.main:main

      [octomotron.script]
      remove = octomotron.remove:config_parser
      rm = octomotron.remove:config_parser
      serve = octomotron.serve:config_parser
      deploy = octomotron.deploy:config_parser
      update = octomotron.update:config_parser
      """
      )
