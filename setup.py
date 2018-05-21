# pylint: disable=no-name-in-module,import-error
import os
import subprocess
import sys
import platform

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

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


def _clean_bins():
    path = os.path.join(os.path.abspath(os.path.curdir), 'pytcg')
    cmd1 = ['make clean']
    for cmd in (cmd1):
        try:
            if subprocess.call(cmd.split(), cwd=path) == 0:
                break
        except OSError:
            continue
    else:
        raise LibError("Unable to clean libtcg build.")


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
    version='0.0.0.1',
    description="A Python interface to libtcg and TCG IR",
    url='https://github.com/angr/pytcg',
    maintainer = 'pwnslinger',
    maintainer_email = 'pwnslinger@asu.edu',
    keywords = ['TCG', 'pytcg', 'angr', 'QEMU'],
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
