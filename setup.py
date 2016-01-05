#!/usr/bin/env python
import os.path

import setuptools

import sprockets.clients.http


def read_requirements(name):
    requirements = []
    try:
        with open(os.path.join('requires', name)) as req_file:
            for line in req_file:
                if '#' in line:
                    line = line[:line.index('#')]
                line = line.strip()
                if line.startswith('-r'):
                    requirements.extend(read_requirements(line[2:].strip()))
                elif line and not line.startswith('-'):
                    requirements.append(line)
    except IOError:
        pass
    return requirements


setuptools.setup(
    name='sprockets.clients.http',
    version=sprockets.clients.http.__version__,
    description='Easily call HTTP APIs',
    long_description='\n'+open('README.rst').read(),
    author='Dave Shawley',
    author_email='daves@aweber.com',
    url='https://github.com/sprockets/sprockets.clients.http',
    license='BSD',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=setuptools.find_packages(),
    namespace_packages=['sprockets', 'sprockets.clients'],
    install_requires=read_requirements('installation.txt'),
    tests_require=read_requirements('testing.txt'),
    test_suite='nose.collector',
    zip_safe=True)
