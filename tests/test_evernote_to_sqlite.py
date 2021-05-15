from click.testing import CliRunner
from evernote_to_sqlite.cli import cli
import sqlite_utils
import pathlib

example_enex = pathlib.Path(__file__).parent / "example-note.enex"
example_broken_enex = pathlib.Path(__file__).parent / "example-note_broken.enex"


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
        "resources_fts_config",
        "resources_fts",
        "resources_fts_idx",
        "resources_fts_data",
        "resources_fts_docsize",
    }
    assert list(db["notes"].rows) == [
        {
            "id": "1ea8b9baeca91343cdb6a12d44f5cdb2edf5f2e5",
            "title": "Example note with images",
            "content": '<en-note><div>This note includes two images. &#353;.</div><div><br /></div><div><span style="font-weight: bold;">The Python logo</span></div><div><br /></div><div><en-media hash="61098c2c541de7f0a907c301dd6542da" type="image/svg+xml" width="125" /><br /></div><div><br /></div><div><span style="font-weight: bold;">The Evernote logo</span></div><div><br /></div><div><en-media hash="91bd26175acac0b2ffdb6efac199f8ca" type="image/svg+xml" width="125" /><br /></div><div><br /></div><div>This image contains text:</div><div><br /></div><div><en-media hash="76dd28b07797cc9f3f129c4871c5293c" type="image/png" /></div><div><br /></div></en-note>',
            "created": "2020-10-11T21:28:22",
            "updated": "2020-10-11T23:30:38",
            "latitude": "37.77742571705006",
            "longitude": "-122.4256495114116",
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
            "reco-type": None,
            "file-name": None,
        },
        {
            "md5": "91bd26175acac0b2ffdb6efac199f8ca",
            "mime": "image/svg+xml",
            "width": "0",
            "height": "0",
            "duration": "0",
            "timestamp": "19700101T000000Z",
            "ocr": None,
            "reco-type": None,
            "file-name": None,
        },
        {
            "md5": "76dd28b07797cc9f3f129c4871c5293c",
            "mime": "image/png",
            "width": "670",
            "height": "128",
            "duration": "0",
            "timestamp": "19700101T000000Z",
            "ocr": "This is so can test the OCR",
            "reco-type": "unknown",
            "file-name": "Untitled-1.png",
        },
    ]
    resource_md5s = [rd["md5"] for rd in db["resources_data"].rows]
    assert resource_md5s == [
        "61098c2c541de7f0a907c301dd6542da",
        "91bd26175acac0b2ffdb6efac199f8ca",
        "76dd28b07797cc9f3f129c4871c5293c",
    ]
    assert list(db["note_resources"].rows) == [
        {
            "note_id": "1ea8b9baeca91343cdb6a12d44f5cdb2edf5f2e5",
            "resource_id": "61098c2c541de7f0a907c301dd6542da",
        },
        {
            "note_id": "1ea8b9baeca91343cdb6a12d44f5cdb2edf5f2e5",
            "resource_id": "91bd26175acac0b2ffdb6efac199f8ca",
        },
        {
            "note_id": "1ea8b9baeca91343cdb6a12d44f5cdb2edf5f2e5",
            "resource_id": "76dd28b07797cc9f3f129c4871c5293c",
        },
    ]
    # Check we enabled Porter stemming
    assert "tokenize='porter'" in db["notes_fts"].schema


def test_recover_proper_enex(tmpdir):
    output = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli, ["recover-enex", output, str(example_enex)], catch_exceptions=False
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
        "resources_fts_config",
        "resources_fts",
        "resources_fts_idx",
        "resources_fts_data",
        "resources_fts_docsize",
    }
    assert list(db["notes"].rows) == [
        {
            "id": "e2d3f11777001291c06f20a1de05772fe0ba5a2c",
            "title": "Example note with images",
            "content": '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"><en-note><div>This note includes two images. &scaron;.</div><div><br /></div><div><span style="font-weight: bold;">The Python logo</span></div><div><br /></div><div><en-media hash="61098c2c541de7f0a907c301dd6542da" type="image/svg+xml" width="125" /><br /></div><div><br /></div><div><span style="font-weight: bold;">The Evernote logo</span></div><div><br /></div><div><en-media hash="91bd26175acac0b2ffdb6efac199f8ca" type="image/svg+xml" width="125" /><br /></div><div><br /></div><div>This image contains text:</div><div><br /></div><div><en-media hash="76dd28b07797cc9f3f129c4871c5293c" type="image/png" /></div><div><br /></div></en-note>',
            "created": "2020-10-11T21:28:22",
            "updated": "2020-10-11T23:30:38",
            "latitude": "37.77742571705006",
            "longitude": "-122.4256495114116",
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
            "reco-type": None,
            "file-name": None,
        },
        {
            "md5": "91bd26175acac0b2ffdb6efac199f8ca",
            "mime": "image/svg+xml",
            "width": "0",
            "height": "0",
            "duration": "0",
            "timestamp": "19700101T000000Z",
            "ocr": None,
            "reco-type": None,
            "file-name": None,
        },
        {
            "md5": "76dd28b07797cc9f3f129c4871c5293c",
            "mime": "image/png",
            "width": "670",
            "height": "128",
            "duration": "0",
            "timestamp": "19700101T000000Z",
            "ocr": "This is so can test the OCR",
            "reco-type": "unknown",
            "file-name": "Untitled-1.png",
        },
    ]
    resource_md5s = [rd["md5"] for rd in db["resources_data"].rows]
    assert resource_md5s == [
        "61098c2c541de7f0a907c301dd6542da",
        "91bd26175acac0b2ffdb6efac199f8ca",
        "76dd28b07797cc9f3f129c4871c5293c",
    ]
    assert list(db["note_resources"].rows) == [
        {
            "note_id": "e2d3f11777001291c06f20a1de05772fe0ba5a2c",
            "resource_id": "61098c2c541de7f0a907c301dd6542da",
        },
        {
            "note_id": "e2d3f11777001291c06f20a1de05772fe0ba5a2c",
            "resource_id": "91bd26175acac0b2ffdb6efac199f8ca",
        },
        {
            "note_id": "e2d3f11777001291c06f20a1de05772fe0ba5a2c",
            "resource_id": "76dd28b07797cc9f3f129c4871c5293c",
        },
    ]
    # Check we enabled Porter stemming
    assert "tokenize='porter'" in db["notes_fts"].schema


def test_recover_broken_enex(tmpdir):
    output = str(tmpdir / "output.db")
    result = CliRunner().invoke(
        cli, ["recover-enex", output, str(example_broken_enex)], catch_exceptions=False
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
        "resources_fts_config",
        "resources_fts",
        "resources_fts_idx",
        "resources_fts_data",
        "resources_fts_docsize",
    }
    assert list(db["notes"].rows) == [
        {
            "id": "0c59e90500da181d5518ec94c68956f23bfd79c2",
            "title": "Example note with images",
            "content": '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"><en-note><div>This note includes two images. &scaron;.</div><div><br /></div><div><span style="font-weight: bold;">The Python logo</span></div><div><br /></div><div><en-media hash="61098c2c541de7f0a907c301dd6542da" type="image/svg+xml" width="125" /><br /></div><div><br /></div><div><span style="font-weight: bold;">The Evernote logo</span></div><div><br /></div><div><en-media hash="91bd26175acac0b2ffdb6efac199f8ca" type="image/svg+xml" width="125" /><br /></div><div><br /></div><div>This image contains text:</div><div><br /></div><div><en-media hash="76dd28b07797cc9f3f129....BROKEN......',
            "created": "2020-10-11T21:28:22",
            "updated": "2020-10-11T23:30:38",
            "latitude": "37.77742571705006",
            "longitude": "-122.4256495114116",
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
            "reco-type": None,
            "file-name": None,
        },
        {
            "md5": "91bd26175acac0b2ffdb6efac199f8ca",
            "mime": "image/svg+xml",
            "width": "0",
            "height": "0",
            "duration": "0",
            "timestamp": "19700101T000000Z",
            "ocr": None,
            "reco-type": None,
            "file-name": None,
        },
        {
            "md5": "76dd28b07797cc9f3f129c4871c5293c",
            "mime": "image/png",
            "width": "670",
            "height": "128",
            "duration": "0",
            "timestamp": "19700101T000000Z",
            "ocr": "This is so can test the OCR",
            "reco-type": "unknown",
            "file-name": "Untitled-1.png",
        },
    ]
    resource_md5s = [rd["md5"] for rd in db["resources_data"].rows]
    assert resource_md5s == [
        "61098c2c541de7f0a907c301dd6542da",
        "91bd26175acac0b2ffdb6efac199f8ca",
        "76dd28b07797cc9f3f129c4871c5293c",
    ]
    assert list(db["note_resources"].rows) == [
        {
            "note_id": "0c59e90500da181d5518ec94c68956f23bfd79c2",
            "resource_id": "61098c2c541de7f0a907c301dd6542da",
        },
        {
            "note_id": "0c59e90500da181d5518ec94c68956f23bfd79c2",
            "resource_id": "91bd26175acac0b2ffdb6efac199f8ca",
        },
        {
            "note_id": "0c59e90500da181d5518ec94c68956f23bfd79c2",
            "resource_id": "76dd28b07797cc9f3f129c4871c5293c",
        },
    ]
    # Check we enabled Porter stemming
    assert "tokenize='porter'" in db["notes_fts"].schema