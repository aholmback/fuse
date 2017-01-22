from setuptools import setup, find_packages
import os

about = {}
with open(os.path.join('fuse', '__about__.py')) as f:
    exec(f.read(), about)

with open(os.path.join('README.rst')) as f:
        long_description = f.read()

requirements = [
        'cement==2.10.2',
        'Jinja2==2.9.4',
        'semantic_version==2.6.0',
        'inflection==0.3.1',
        'six==1.10.0',
    ]

setup(
    name=about['__title__'],
    version=about['__version__'],

    description=about['__summary__'],
    long_description=long_description,
    license=about['__license__'],
    url=about['__uri__'],

    author=about['__author__'],
    author_email=about['__email__'],

    classifiers=[
        'Development Status :: 1 - Planning',
    ],

    packages=find_packages(),
    include_package_data=True,

    install_requires=requirements,

    entry_points={
        'console_scripts': [
            'fuse = fuse.__main__:main',
        ],
    },
)
