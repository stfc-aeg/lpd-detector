"""Setup script for lpd python package."""

from setuptools import setup, find_packages
import versioneer

with open('requirements.txt') as f:
   required = f.read().splitlines()

setup(name='lpd',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='STFC LPD',
      url='https://github.com/stfc-aeg/lpd-detector.git',
      author='Tim Nicholls',
      author_email='tim.nicholls@stfc.ac.uk',
      packages=find_packages(),
      install_requires=required,
      zip_safe=False
)
