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
    name='mlgb.indexer',
    version=version,
    description=description,
    long_description=longdesc,
    author='Michael Davis',
    author_email='michael.davis@bodleian.ox.ac.uk',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['mlgb'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'MySQL-python',
    ],
    extras_require={
        'test': ['pytest', ],
    },
    entry_points={
        'console_scripts': [
            'set_index_book_ids=mlgb.indexer.setIndexBookIDs:setBookIDs',
            'strip_xml_comments=mlgb.indexer.stripXMLcomments:stripComments',
            'strip_unwanted_tags=mlgb.indexer.stripUnwantedFormatting:stripUnwantedTags',
            'write_xml=mlgb.indexer.authortitle_to_xml:writeXML',
            'write_html=mlgb.indexer.writeHTML:writeAllHTMLFiles',
            'catalogues_html=mlgb.indexer.cataloguesHTML:writeAllHTMLFiles',
            'write_static_html=mlgb.indexer.write_static_mlgb:writeStaticHTML',
        ],
    },
    classifiers=[
        'Programming Language :: Python',
        'License :: Other/Proprietary License',
        'Development Status :: 3 - Alpha',
    ],
)

