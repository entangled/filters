#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="entangled-filters",
    version="0.4",
    packages=find_packages(),

    install_requires=[],
    # include_package_data=True,
    # package_data={
    #     # If any package contains *.txt or *.rst files, include them:
    #     '': ['*.txt', '*.rst'],
    #     # And include any *.msg files found in the 'hello' package, too:
    #     'hello': ['*.msg'],
    # },

    # metadata to display on PyPI
    author="Johan Hidding",
    author_email="j.hidding@esciencecenter.nl",
    description="Set of Pandoc filters to aid in literate programming",
    keywords="literate programming",
    url="https://entangled.github.io/",   # project home page, if any
    project_urls={
          "Bug Tracker": "https://github.com/entangled/filters/issues/"
        , "Documentation": "https://entangled.github.io/filters/"
        , "Source Code": "https://github.com/entangled/filters/"
    },
    classifiers=[
          'License :: OSI Approved :: Apache Software License'
        , 'Development Status :: 3 - Alpha'
        , 'Intended Audience :: Science/Research'
        , 'Intended Audience :: Developers'
        , 'Environment :: Console'
        , 'Natural Language :: English'
        , 'Operating System :: OS Independent'
        , 'Programming Language :: Python :: 3.7'
        , 'Programming Language :: Python :: 3.8'
        , 'Topic :: Education'
        , 'Topic :: Documentation'
        , 'Topic :: Scientific/Engineering'
        , 'Topic :: Software Development'
        , 'Topic :: Software Development :: Documentation'
        , 'Topic :: Software Development :: Testing'
        , 'Topic :: Text Processing :: Markup'
    ],

    entry_points = {
        'console_scripts': [
              'pandoc-tangle=entangled.tangle:main'
            , 'pandoc-test=entangled.doctest:main'
        ]
    }
    # could also include long_description, download_url, etc.
)

