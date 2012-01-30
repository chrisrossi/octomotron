
from setuptools import setup, find_packages

setup(name='buildout_octomotron',
      version='0.0',
      packages=find_packages(),
      zip_safe=False,
      entry_points = """\
      [zc.buildout.extension]
      ext = octomotron_buildout:extension
      """
      )
