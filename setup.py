from setuptools import setup, find_packages

version = '0.1.0'

setup(
    name="helga-oral-history",
    version=version,
    description=('A (mosty) good recounting of what helga heas'),
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='irc bot oral-history',
    author='Justin Caratzas',
    author_email='bigjust@lambdaphil.es',
    license='LICENSE',
    packages=find_packages(),
    include_package_data=True,
    py_modules=['helga_oral_history'],
    zip_safe=True,
    entry_points = dict(
        helga_plugins = [
            'oral_history = helga_oral_history:oral_history',
        ],
    ),
)
