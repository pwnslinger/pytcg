# pylint: disable=no-name-in-module,import-error
import os
import subprocess
import sys
import glob
import time
from urllib import urlopen
import tarfile
import platform
import shutil
PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
LIB_DIR = os.path.join(PROJECT_DIR, 'pyvex', 'lib')
INCLUDE_DIR = os.path.join(PROJECT_DIR, 'pyvex', 'include')

try:
    from setuptools import setup
    from setuptools import find_packages
    packages = find_packages()
except ImportError:
    from distutils.core import setup
    packages = []
    for root, _, filenames in os.walk(PROJECT_DIR):
        if "__init__.py" in filenames:
            packages.append(root)

from distutils.util import get_platform
from distutils.errors import LibError
from distutils.command.build import build as _build
from distutils.command.sdist import sdist as _sdist

TCG_PATH = os.path.join(PROJECT_DIR, 'pytcg', 'libtcg')
README_PATH = os.path.join(PROJECT_DIR, 'README.md')

try:
    with open(README_PATH, 'r') as f:
        readme = f.read()
except:
    readme = ""


VEX_PATH = os.path.abspath(os.path.join(PROJECT_DIR, '..', 'vex'))

if not os.path.exists(VEX_PATH):
    VEX_PATH = os.path.join(PROJECT_DIR, 'vex')

if not os.path.exists(VEX_PATH):
    VEX_PATH = os.path.join(PROJECT_DIR, 'vex-master')

if not os.path.exists(VEX_PATH):
    sys.__stderr__.write('###########################################################################\n')
    sys.__stderr__.write('WARNING: downloading vex sources directly from github.\n')
    sys.__stderr__.write('If this strikes you as a bad idea, please abort and clone the angr/vex repo\n')
    sys.__stderr__.write('into the same folder containing the pyvex repo.\n')
    sys.__stderr__.write('###########################################################################\n')
    sys.__stderr__.flush()
    time.sleep(10)

    VEX_URL = 'https://github.com/angr/vex/archive/master.tar.gz'
    with open('vex-master.tar.gz', 'wb') as v:
        v.write(urlopen(VEX_URL).read())
    with tarfile.open('vex-master.tar.gz') as tar:
        tar.extractall()

def _clean_bins():
    shutil.rmtree(LIB_DIR, ignore_errors=True)
    shutil.rmtree(INCLUDE_DIR, ignore_errors=True)

'''
def _copy_sources():
    local_vex_path = os.path.join(PROJECT_DIR, 'vex')
    assert local_vex_path != VEX_PATH
    shutil.rmtree(local_vex_path, ignore_errors=True)
    os.mkdir(local_vex_path)

    vex_src = ['LICENSE.GPL', 'LICENSE.README', 'Makefile-gcc', 'Makefile-msvc', 'common.mk', 'pub/*.h', 'priv/*.c', 'priv/*.h', 'auxprogs/*.c']
    for spec in vex_src:
        dest_dir = os.path.join(local_vex_path, os.path.dirname(spec))
        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir)
        for srcfile in glob.glob(os.path.join(VEX_PATH, spec)):
            shutil.copy(srcfile, dest_dir)
'''
def _build_tcg():
    e = os.environ.copy()

    cmd1 = ['./build.sh']
    for cmd in (cmd1):
        try:
            if subprocess.call(cmd, cwd=TCG_PATH, env=e) == 0:
                break
        except OSError:
            continue
    else:
        raise LibError("Unable to build libtcg.")


def _build_ffi():
    path = os.path.abspath(os.path.curdir)
    sys.path.insert(0, os.path.join(path))
    import gen_cffi
    try:
        gen_cffi.doit()
    except Exception as e:
        print(repr(e))
        raise

class build(_build):
    def run(self):
        path = os.path.abspath(os.path.curdir)
        self.execute(_build_tcg, (), msg="Building libtcg")
        os.chdir(os.path.join(path, 'pytcg'))
        self.execute(_build_ffi, (), msg="Creating CFFI defs file")
        os.chdir(path)
        _build.run(self)


class sdist(_sdist):
    def run(self):
        self.execute(_clean_bins, (), msg="Removing binaries")
        #self.execute(_copy_sources, (), msg="Copying VEX sources")
        _sdist.run(self)

cmdclass = { 'build': build, 'sdist': sdist}

try:
    from setuptools.command.develop import develop as _develop
    from setuptools.command.bdist_egg import bdist_egg as _bdist_egg
    class develop(_develop):
        def run(self):
            self.execute(_build_tcg, (), msg="Building libtcg")
            self.execute(_build_ffi, (), msg="Creating CFFI defs file")
            _develop.run(self)
    cmdclass['develop'] = develop

    class bdist_egg(_bdist_egg):
        def run(self):
            self.run_command('build')
            _bdist_egg.run(self)
    cmdclass['bdist_egg'] = bdist_egg
except ImportError:
    print("Proper 'develop' support unavailable.")

if 'bdist_wheel' in sys.argv and '--plat-name' not in sys.argv:
    sys.argv.append('--plat-name')
    name = get_platform()
    if 'linux' in name:
        # linux_* platform tags are disallowed because the python ecosystem is fubar
        # linux builds should be built in the centos 5 vm for maximum compatibility
        sys.argv.append('manylinux1_' + platform.machine())
    else:
        # https://www.python.org/dev/peps/pep-0425/
        sys.argv.append(name.replace('.', '_').replace('-', '_'))

setup(
    name="pytcg",
    version="0.0.0.8",
    description="A Python interface to libtcg and TCG IR",
    url='https://github.com/angr-tcg/pytcg',
    packages=packages,
    cmdclass=cmdclass,
    long_description=readme,
    install_requires=[
        'pycparser',
        'cffi>=1.0.3',
        'archinfo>=7.8.2.21',
        'bitstring',
        'future',
    ],
    setup_requires=[ 'pycparser', 'cffi>=1.0.3' ],
    include_package_data=True,
    package_data={
        'pytcg': ['__init__.py', 'gen_cffi.py','*.so', 'libtcg/build.sh', 'libtcg/*.so.*', 'inc/*'],
    },
)
