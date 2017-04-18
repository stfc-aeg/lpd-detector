from setuptools import setup, find_packages, Extension
from distutils.command.build_ext import build_ext
from distutils.command.clean import clean
from distutils import log
import versioneer

import os
import glob
import sys
import subprocess
import shlex

stub_only = False
if '--stub-only' in sys.argv:
    stub_only = True
    sys.argv.remove('--stub-only')
    
# Define the stub fem_api extension modules 
fem_api_extension_path='fem_api_extension'
fem_api_wrapper_source = os.path.join(fem_api_extension_path, 'fem_api_wrapper.c')

fem_api_stub_source_path=os.path.join(fem_api_extension_path, 'api_stub')
fem_api_stub_sources = [fem_api_wrapper_source] + [
                            os.path.join(fem_api_stub_source_path, source) for source in [
                                'femApi.cpp', 'ExcaliburFemClient.cpp', 'FemApiError.cpp']
                             ]

fem_api_stub = Extension('excalibur.fem_api_stub', 
    sources=fem_api_stub_sources,
    include_dirs=[fem_api_stub_source_path],
    define_macros=[('COMPILE_AS_STUB', None)],
)

# Add the stub to the list of extension modules to build
fem_ext_modules = [fem_api_stub]

# If the stub_only option is not set, define the full fem_api extension module and add to the list
if not stub_only:
    
    fem_api_path=os.path.join(fem_api_extension_path, 'api')
    fem_api_source_path=os.path.join(fem_api_path, 'src')
    fem_api_include_path=os.path.join(fem_api_path, 'include')
    
    fem_api_sources = [fem_api_wrapper_source] 
    
    fem_api = Extension('excalibur.fem_api',
        sources=fem_api_sources,
        include_dirs=[fem_api_include_path], 
        library_dirs=[],
        libraries=[], 
        define_macros=[],
    )

    fem_ext_modules.append(fem_api)
  
class ExcaliburBuildExt(build_ext):
    
    def run(self):

        # Precompile the API library if necessary        
        if not stub_only:
            self.precompile_api_library(fem_api)
            
        # Run the real build_ext command
        build_ext.run(self)
        
    def precompile_api_library(self, fem_api_ext):
        
        log.info("Pre-compiling FEM API library")

        # If BOOST_ROOT set in environment, set up so we can pass into Makefile 
        if 'BOOST_ROOT' in os.environ:
            boost_root = os.environ['BOOST_ROOT']
        else:
            boost_root = None
                    
        # Set and create object compile path
        build_temp_obj_path = os.path.abspath(os.path.join(self.build_temp, 'fem_api', 'obj'))
        self.makedir(build_temp_obj_path)
            
        # Set and create the library output path
        build_temp_lib_path = os.path.abspath(os.path.join(self.build_temp, 'fem_api', 'lib'))
        self.makedir(build_temp_lib_path)
        
        # Build the make command
        make_cmd = 'make OBJ_DIR={} LIB_DIR={}'.format(build_temp_obj_path, build_temp_lib_path)
        if boost_root:
            make_cmd = make_cmd + ' BOOST_ROOT={}'.format(boost_root)
        
        # Run the make command
        subprocess.call(shlex.split(make_cmd), cwd=fem_api_path)
        
        # Inject the appropriate paths and libraries into the Extension configuration
        fem_api_ext.library_dirs.append(build_temp_lib_path)

        if boost_root:        
            fem_api_ext.library_dirs.append(os.path.join(boost_root, 'lib'))
            
        fem_api_ext.libraries.extend(['boost_system', 'boost_thread', 'fem_api'])
        
    def makedir(self, path):
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise
        
class ExcaliburClean(clean):
    
    def run(self):

        target_path = 'excalibur'
        ext_targets = [os.path.join(target_path, lib_name) for lib_name in ['fem_api.so', 'fem_api_stub.so']]
        
        for ext_target in ext_targets:
            if os.path.exists(ext_target):
                print('removing {}'.format(ext_target))
                os.remove(ext_target)
                                   
        clean.run(self)        
        
setup(
    name='excalibur',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='EXCALIBUR detector plugin for ODIN framework',
    url='https://github.com/stfc-aeg/odin-excalibur',
    author='Tim Nicholls',
    author_email='tim.nicholls@stfc.ac.uk',
    ext_modules=fem_ext_modules,
    packages=find_packages(),
    install_requires=['odin==0.2'],
    dependency_links=['https://github.com/percival-detector/odin/zipball/0.2#egg=odin-0.2'],
    extras_require={
      'test': ['nose', 'coverage', 'mock'],  
    },
    cmdclass = { 
        'build_ext' : ExcaliburBuildExt,
        'clean' : ExcaliburClean,
        },
)
