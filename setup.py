from setuptools import setup
import os

VERSION = "0.2"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="evernote-to-sqlite",
    description="Tools for converting Evernote content to SQLite",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/dogsheep/evernote-to-sqlite",
    project_urls={
        "Issues": "https://github.com/dogsheep/evernote-to-sqlite/issues",
        "CI": "https://github.com/dogsheep/evernote-to-sqlite/actions",
        "Changelog": "https://github.com/dogsheep/evernote-to-sqlite/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["evernote_to_sqlite"],
    entry_points="""
        [console_scripts]
        evernote-to-sqlite=evernote_to_sqlite.cli:cli
    """,
    install_requires=["click", "sqlite-utils"],
    extras_require={"test": ["pytest"]},
    tests_require=["evernote-to-sqlite[test]"],
)
