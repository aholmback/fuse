from setuptools import setup, find_packages

setup(
    name='fuse',
    description="Framework for developing applications that combine, transform and generate a structure of configuration files based on a set of predefined interacting components.",
    version='0.0.2-alpha.15',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'fuse = fuse.__main__:main',
        ],
    },
    install_requires = [
        'blinker==1.4',
        'cement==2.10.2',
        'Jinja2==2.9.4',
        'semantic_version==2.6.0',
        'inflection==0.3.1',
        'peewee==2.8.5',
        'six==1.10.0',
    ],
)
