import os
from setuptools import setup
from setuptools import find_packages

version = open(
    os.path.join("mlgb", "indexer", "version.txt")
).read().strip()

description = "Indexing scripts for mlgb."

longdesc = open("README.md").read()
longdesc += open(os.path.join("docs", "HISTORY.rst")).read()

setup(
    name='bodleian.vocabularies',
    version=version,
    description=description,
    long_description=longdesc,
    author='Michael Davis',
    author_email='michael.davis@bodleian.ox.ac.uk',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['mlgb'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    extras_require={
        'test': ['pytest', ],
    },
    classifiers=[
        'Programming Language :: Python',
        'License :: Other/Proprietary License',
        'Development Status :: 3 - Alpha',
    ],
)
