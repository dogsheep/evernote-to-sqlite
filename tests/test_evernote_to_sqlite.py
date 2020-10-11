from click.testing import CliRunner
from evernote_to_sqlite.cli import cli
import sqlite_utils
import pathlib

example_enex = pathlib.Path(__file__).parent / "example-note.enex"


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert 0 == result.exit_code
        assert result.output.startswith("cli, version ")


def test_enex(tmpdir):
    output = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli, ["enex", output, str(example_enex)], catch_exceptions=False
    )
    assert 0 == result.exit_code
    db = sqlite_utils.Database(output)
    assert set(db.table_names()) == {
        "notes",
        "resources",
        "resources_data",
        "note_resources",
        "notes_fts_idx",
        "notes_fts",
        "notes_fts_config",
        "notes_fts_docsize",
        "notes_fts_data",
    }
    assert list(db["notes"].rows) == [
        {
            "id": "54ac334082cd0013c4d3898649d12d45d95f966c",
            "title": "Example note with images",
            "content": '<en-note><div>This note includes two images.</div><div><br /></div><div><b>The Python logo</b></div><div><br /></div><div><en-media hash="61098c2c541de7f0a907c301dd6542da" type="image/svg+xml" width="125" /></div><div><br /></div><div><b>The Evernote logo</b></div><div><br /></div><div><en-media hash="91bd26175acac0b2ffdb6efac199f8ca" type="image/svg+xml" width="125" /></div><div><br /></div></en-note>',
            "created": "2020-10-11T21:28:22",
            "updated": "2020-10-11T21:30:26",
            "latitude": "37.7",
            "longitude": "-122.4",
            "altitude": "23.16121864318848",
            "author": "Simon Willison",
            "source": "desktop.mac",
            "reminder-order": "0",
        }
    ]
    assert list(db["resources"].rows) == [
        {
            "md5": "61098c2c541de7f0a907c301dd6542da",
            "mime": "image/svg+xml",
            "width": "0",
            "height": "0",
            "duration": "0",
            "timestamp": "19700101T000000Z",
            "ocr": None,
        },
        {
            "md5": "91bd26175acac0b2ffdb6efac199f8ca",
            "mime": "image/svg+xml",
            "width": "0",
            "height": "0",
            "duration": "0",
            "timestamp": "19700101T000000Z",
            "ocr": None,
        },
    ]
    assert list(db["resources_data"].rows) == [
        {
            "md5": "61098c2c541de7f0a907c301dd6542da",
            "data": b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\naria-label="Python" role="img"\nviewBox="0 0 512 512"><rect\nwidth="512" height="512"\nrx="15%"\nfill="#fff"/><g fill="#5a9fd4"><path id="p" d="M254 64c-16 0-31 1-44 4-39 7-46 21-46 47v35h92v12H130c-27 0-50 16-58 46-8 35-8 57 0 93 7 28 23 47 49 47h32v-42c0-30 26-57 57-57h91c26 0 46-21 46-46v-88c0-24-21-43-46-47-15-3-32-4-47-4zm-50 28c10 0 17 8 17 18 0 9-7 17-17 17-9 0-17-8-17-17 0-10 8-18 17-18z"/></g><use xlink:href="#p" fill="#ffd43b" transform="rotate(180,256,255)"/></svg>',
        },
        {
            "md5": "91bd26175acac0b2ffdb6efac199f8ca",
            "data": b'<svg xmlns="http://www.w3.org/2000/svg"\naria-label="Evernote" role="img"\nviewBox="0 0 512 512"><rect\nwidth="512" height="512"\nrx="15%"\nfill="#46c850"/><path d="m121 143h35c3 0 4-1 4-4l-1-38c0-10 6-19 6-19h-1l-68 67v1s10-7 25-7zm271-6c-3-15-12-23-20-25-32-8-65-12-98-11-2-19-18-29-54-29-31-1-49 6-49 29v39c0 8-5 13-14 13h-34c-7 0-13 2-18 4-4 2-14 7-14 30-1 19 13 95 23 115 3 9 6 12 14 15 16 8 54 15 73 18 17 2 28 6 36-8 2-4 10-30 9-52 0-1 2-2 2 0 0 7-2 36 19 43l45 9c16 1 28 7 28 49 0 25-6 28-34 28-22 0-30 1-30-17 0-14 14-13 25-13 4 0 1-3 1-12s5-14 0-14c-36-1-58 0-58 45 0 42 16 49 68 49 40 0 55-1 71-52 25-78 18-205 9-253zm-46 115c-5-6-31-8-40-4 2-10 6-22 22-22 15 0 18 16 18 26z" fill="#4b4b4b"/></svg>',
        },
    ]
    assert list(db["note_resources"].rows) == [
        {
            "note_id": "54ac334082cd0013c4d3898649d12d45d95f966c",
            "resource_id": "61098c2c541de7f0a907c301dd6542da",
        },
        {
            "note_id": "54ac334082cd0013c4d3898649d12d45d95f966c",
            "resource_id": "91bd26175acac0b2ffdb6efac199f8ca",
        },
    ]
