import sys
try:
    from setuptools import setup
except ImportError:
    from distutils import setup

install_requires = [
    'Flask',
    'Flask-SQLAlchemy',
    'inflection>=0.1.2',
    'WTForms'
]

if sys.version_info < (2, 6):
    install_requires.append('simplejson')

setup(
    name='Flask-GenericViews',
    version='0.1.22',
    description='Generic Views for Flask',
    long_description=__doc__,
    author='Konsta Vesterinen',
    author_email='konsta.vesterinen@gmail.com',
    url='http://github.com/kvesteri/flask-generic-views',
    packages=['flask_generic_views'],
    include_package_data=True,
    license='BSD',
    zip_safe=False,
    platforms='any',
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
