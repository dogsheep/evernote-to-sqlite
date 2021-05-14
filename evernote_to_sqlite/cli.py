import sqlite_utils
import click
import os
from .utils import find_all_tags, save_note, ensure_indexes
import time
import datetime as dt
from .hugexmlparser import HugeXmlParser, read_recovery_file, update_recovery_file
import logging
from rich.logging import RichHandler
from rich.progress import Progress
import lxml

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

MEGABYTE = 1_000_000


@click.group()
@click.version_option()
def cli():
    """Tools for converting Evernote content to SQLite"""


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
    """Convert Evernote .enex exports to SQLite"""
    file_length = os.path.getsize(enex_file)
    fp = open(enex_file, "r", encoding="utf-8")
    db = sqlite_utils.Database(db_path)
    with click.progressbar(length=file_length, label="Importing from ENEX") as bar:
        for tag, note in find_all_tags(fp, ["note"], progress_callback=bar.update):
            save_note(db, note)
    fp.close()
    ensure_indexes(db)


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
@click.option(
    "--max_note_size",
    type=click.INT,
    required=False,
    default=30,
    help="This maximum size on MB attempting to discover end-tag of recognised note before skipping to next.",
)
@click.option(
    "--resume_file",
    type=click.Path(),
    required=False,
    help="Allows resume where conversion was aborted/failed. File will be created if it does not exist and will register start, end byte in Enex file.",
)
def recover_enex(db_path, enex_file, max_note_size=30, resume_file=None):
    """Use recover techniques allowing malformed Evernote exports to be transformed to SQLite and specficially useful for very large Enex file. Be warned that this takes a very long time for larges Enex files."""

    with Progress() as progress:
        task1 = progress.add_task("[red]Downloading...", total=1000)
        task2 = progress.add_task("[green]Processing...", total=1000)
        task3 = progress.add_task("[cyan]Cooking...", total=1000)

        while not progress.finished:
            progress.update(task1, advance=0.5)
            progress.update(task2, advance=0.3)
            progress.update(task3, advance=0.9)
            progress.console.print(f"Working on job #{dt.datetime.now().isoformat()}")
            time.sleep(0.01)

    file_length = os.path.getsize(enex_file)
    db = sqlite_utils.Database(db_path)
    fp = open(enex_file, "r", encoding="utf-8")

    records = read_recovery_file()
    last_start = sorted(records)[-1][0] if records else 0
    count = len(records) - 1
    splitted = 0
    content_escaped = 0

    xml_parser = HugeXmlParser(enex_file)

    for start_pos, end_pos, data in xml_parser.yield_tag(start_pos=last_start):
        logger.info(
            f"{count}: {round(len(data) / MEGABYTE, 1)} MB,"
            f"recovered: {xml_parser.new_start}, exceed max size: {xml_parser.exceed_max}"
        )
        records.add((start_pos, end_pos))
        update_recovery_file(records)
        notes = []
        try:
            notes.append(etree.fromstring(data))
        except lxml.etree.XMLSyntaxError as e:
            logger.error(e)
            logger.warning("potential multiple notes breaking these up")
            splitted += 1
            for data_chunk in xml_parser.split_multiple_tag_chunk(data):
                try:
                    data_chunk = etree.fromstring(data_chunk)
                except lxml.etree.XMLSyntaxError as e:
                    logger.debug(e)
                    logger.warning("invalid xml, attempt to escaping content-tag")
                    data_chunk = xml_parser.escape_single_tag(data_chunk, "content")
                    content_escaped += 1
                    data_chunk = lxml.etree.fromstring(data_chunk)
                notes.append(data_chunk)
        for note in notes:
            save_note(db, note)
            print(f"saved {count}")
            count += 1
    logger.info(f"Notes with new start generated: {xml_parser.new_start}")
    logger.info(f"Notes that exceeded the maximum size: {xml_parser.exceed_max}")
    logger.info(f"Notes that were found but required splitting: {splitted}")
    logger.info(
        f"Notes found where <content> tag required to be escaped: {content_escaped}"
    )

    fp.close()
    ensure_indexes(db)
