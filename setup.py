__author__ = 'michel'
from setuptools import setup, find_packages

setup(name='comba_clientapi',
      version='0.1',
      description='Comba client api',
      long_description='Provides an interface to the comba controller',
      url='https://gitlab.janguo.de/comba/comba-python-clientapi',
      author='Michael Liebler',
      author_email='michael-liebler@janguo.de',
      license='GPLv3',
      packages=find_packages(exclude=['example']),
      zip_safe=False)
