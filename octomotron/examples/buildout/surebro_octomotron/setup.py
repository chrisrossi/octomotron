from setuptools import setup, find_packages


setup(name='surebro_octomotron',
      version='0.0',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[],
      tests_require=[],
      entry_points="""\
      [octomotron.build]
      build = surebro_octomotron:Build
      """
      )
