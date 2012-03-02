import flask_generic_views

try:
    from setuptools import setup
except ImportError:
    from distutils import setup


setup(
    name='Flask-GenericViews',
    version=flask_generic_views.__version__,
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
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'inflection==0.1.1',
        'WTForms'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
