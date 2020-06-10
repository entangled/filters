#!/usr/bin/env python

from setuptools import setup, find_packages

test_deps = [
      "pytest>=5,<6"
    , "pytest-cov>=2.8.1,<3"
    , "pytest-mypy>=0.4.2,<1"
    , "flake8>=3,<4"
    , "ipykernel>=5.1.3,<6" ]

setup(
    name="entangled-filters",
    version="0.8.0",
    packages=find_packages(),

    install_requires=[
          "jupyter_client>=5.3.4,<6"
        , "pampy>=0.3.0,<0.4"
        , "panflute==1.11.2"
    ],
    tests_require=test_deps,
    extras_require={
        "test": test_deps
    },
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
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
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
            , 'pandoc-doctest=entangled.doctest_main:main'
            , 'pandoc-bootstrap=entangled.bootstrap:main'
            , 'pandoc-annotate-codeblocks=entangled.annotate:main'
            , 'pandoc-inject=entangled.inject:main'
        ]
    },
    include_package_data=True
    # could also include long_description, download_url, etc.
)

