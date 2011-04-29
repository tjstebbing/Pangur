"""
Pangur is a micro-framework for making web applications with python.

Pangur makes use of werkzeug, jinja2, sqlalchemy and WTForms to provide
a simple to use framework that does not get in your way.

"""

from setuptools import setup

setup(
    name = "Pangur",
    version = "0.0.1",
    author = "Pomke",
    author_email = "pomke@pomke.com",
    description = ("A simple micro-framework for building web applications."),
    license = "MIT",
    url = "http://github.com/pomke/Pangur",
    packages=['pangur'],
    long_description=__doc__,
    scripts = ['bin/pangur'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ],
)
