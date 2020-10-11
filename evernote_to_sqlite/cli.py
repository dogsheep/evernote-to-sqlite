import sqlite_utils
import click
import os
from .utils import find_all_tags, save_note, ensure_indexes


@click.group()
@click.version_option()
def cli():
    "Tools for converting Evernote content to SQLite"


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument(
    "enex_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
def enex(db_path, enex_file):
    "Convert Evernote .enex exports to SQLite"
    file_length = os.path.getsize(enex_file)
    fp = open(enex_file)
    db = sqlite_utils.Database(db_path)
    with click.progressbar(length=file_length, label="Importing from ENEX") as bar:
        for tag, note in find_all_tags(fp, ["note"], progress_callback=bar.update):
            save_note(db, note)
    fp.close()
    ensure_indexes(db)
