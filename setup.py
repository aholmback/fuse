from setuptools import setup

setup(
    name='synthesis',
    version='0.0.1',
    entry_points={
        'console_scripts': [
            'synthesis = synthesis.__main__:main',
        ],
    },
    install_requires = [
        'click==6.0'
        'blinker==1.4'
        'cement==2.10.2'
        'Jinja2==2.9.4'
        'semantic_version==2.6.0'
    ],
)