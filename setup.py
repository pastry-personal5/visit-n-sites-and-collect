from setuptools import setup, find_packages

setup(
    name='visit_n_sites_an_collect',
    version='1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'requests',
    ],
)