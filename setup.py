import sys
import subprocess

import distribute_setup
distribute_setup.use_setuptools()

from setuptools import Command, setup


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)


setup(
    name='Flask-GenericViews',
    version='0.1.12',
    description='Generic Views for Flask',
    long_description=__doc__,
    author='Konsta Vesterinen',
    author_email='konsta.vesterinen@gmail.com',
    url='http://github.com/LiiquOy/flask-generic-views',
    packages=['flask_generic_views'],
    include_package_data=True,
    license='BSD',
    zip_safe=False,
    platforms='any',
    install_requires=[
        'setuptools',
        'Flask',
        'Flask-SQLAlchemy'
    ],
    cmdclass={
        'test': PyTest
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
