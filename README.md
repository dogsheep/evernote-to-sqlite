# evernote-to-sqlite

[![PyPI](https://img.shields.io/pypi/v/evernote-to-sqlite.svg)](https://pypi.org/project/evernote-to-sqlite/)
[![Changelog](https://img.shields.io/github/v/release/dogsheep/evernote-to-sqlite?include_prereleases&label=changelog)](https://github.com/dogsheep/evernote-to-sqlite/releases)
[![Tests](https://github.com/dogsheep/evernote-to-sqlite/workflows/Test/badge.svg)](https://github.com/dogsheep/evernote-to-sqlite/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/dogsheep/evernote-to-sqlite/blob/master/LICENSE)

Tools for converting Evernote content to SQLite. See [Building an Evernote to SQLite exporter](https://simonwillison.net/2020/Oct/16/building-evernote-sqlite-exporter/) for background on this project.

## Installation

Install this tool using `pip`:

    $ pip install evernote-to-sqlite

## Usage

Currently the only available command is `evernote-to-sqlite enex`, which converts Evernote's ENEX export files into a SQLite database.

You can create an ENEX export in the Evernote desktop application by selecting some notes (or all of your notes) and using the `File -> Export Notes...` menu option.

You can convert that file to SQLite like so:

    $ evernote-to-sqlite enex evernote.db MyNotes.enex

This will display a progress bar and create a SQLite database file called `evernote.db`.

In situations where the ENEX file being malformed 
or size of notes grown bigger than the optimised XML parser
you have an option to run in recovery mode that will use methods
that will allow the process to carry on through all notes.

    $ evernote-to-sqlite recover-enex evernote.db MyNotes.enex
    
If you have very large file you can also supply a resume-file that allows
the process to process where it left of in such case of interruption.

```shell script
$ evernote-to-sqlite recover-enex --help                                                                   
Usage: evernote-to-sqlite recover-enex [OPTIONS] DB_PATH ENEX_FILE

  Use recover techniques allowing malformed Evernote exports to be transformed
  to SQLite and specifically useful for very large Enex file. Be warned that
  this takes a very long time for larges Enex files.

Options:
  --max_note_size INTEGER  This maximum size on MB attempting to discover end-
                           tag of recognised note before skipping to next.
  --resume_file PATH       Allows resume where conversion was
                           aborted/failed.File will be created if it does not
                           exist and will register start, end byte in Enex
                           file.
  --help                   Show this message and exit.

$ evernote-to-sqlite recover-enex evernote.db MyNotes.enex --max_note_size 30 --resume_file my_resume_file

...

5763: 0.3 MB,recovered: 0, exceed max size: 16
processing current content 1: 1 MB
processing current content 1: 2 MB
processing current content 1: 3 MB
5764: 3.2 MB,recovered: 0, exceed max size: 16
5765: 0.0 MB,recovered: 0, exceed max size: 16
processing current content 1: 1 MB
processing current content 1: 2 MB
processing current content 1: 3 MB
5766: 3.4 MB,recovered: 0, exceed max size: 16
[07:22:40] INFO     Notes with new start generated: 0                                                                                                             cli.py:150
[07:22:41] INFO     Notes that exceeded the maximum size: 16                                                                                                      cli.py:151
           INFO     Notes that were found but required splitting: 51                                                                                              cli.py:152
           INFO     Notes found where <content> tag required to be escaped: 7                                                                                     cli.py:154
Processing Evernote export file 5GB... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸ 100% 0:00:01
Parsing note...                        ━━━━╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  10% 0:00:00
```


### Limitations

Unfortunately the ENEX export format does not include a unique identifier for each note. This means you cannot use this tool to re-import notes after they have been updated - you should consider this tool to be a one-time transformation of an ENEX file into an equivalent SQLite database.

ENEX exports also do not include details of which notebook a note belongs to.

## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:

    cd evernote-to-sqlite
    python -mvenv venv
    source venv/bin/activate

Or if you are using `pipenv`:

    pipenv shell

Now install the dependencies and tests:

    pip install -e '.[test]'

To run the tests:

    pytest
