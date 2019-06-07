"""Setup script for lpd python package."""

from setuptools import setup, find_packages
import versioneer

with open('requirements.txt') as f:
   required = f.read().splitlines()

setup(name='lpd',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='STFC LPD GUI Framework',
    url='https://github.com/stfc-aeg/lpd-detector.git',
    author='Tim Nicholls',
    author_email='tim.nicholls@stfc.ac.uk',
    packages=find_packages(),
    install_requires=required,
    entry_points = {
      'console_scripts': [
            'lpd_fem_gui = lpd.gui.gui:main',
      ]
     },
     zip_safe=False,
)
