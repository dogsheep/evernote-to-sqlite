from xml.etree import ElementTree as ET
import base64
import datetime
import hashlib


def find_all_tags(fp, tags, progress_callback=None):
    parser = ET.XMLPullParser(("start", "end"))
    root = None
    while True:
        chunk = fp.read(1024 * 1024)
        if not chunk:
            break
        parser.feed(chunk)
        for event, el in parser.read_events():
            if event == "start" and root is None:
                root = el
            if event == "end" and el.tag in tags:
                yield el.tag, el
            root.clear()
        if progress_callback is not None:
            progress_callback(len(chunk))


def save_note(db, note):
    title = note.find("title").text
    created = note.find("created").text
    updated = note.find("updated").text
    # Some content has &nbsp; which breaks the XML parser
    content_xml = note.find("content").text.replace("&nbsp;", "")
    content = ET.tostring(ET.fromstring(content_xml)).decode("utf-8")
    row = {
        "title": title,
        "content": content,
        "created": convert_datetime(created),
        "updated": convert_datetime(updated),
    }
    attributes = note.find("note-attributes")
    if attributes is not None:
        row.update({attribute.tag: attribute.text for attribute in attributes})
    # If any of those attributes end in -date, e.g. 'subject-date', convert them
    for key in row:
        if key.endswith("-date"):
            row[key] = convert_datetime(row[key])
    note_id = db["notes"].insert(row, hash_id="id", replace=True, alter=True).last_pk
    # Now do the resources
    for resource in note.findall("resource"):
        resource_id = save_resource(db, resource)
        db["note_resources"].insert(
            {
                "note_id": note_id,
                "resource_id": resource_id,
            },
            pk=("note_id", "resource_id"),
            foreign_keys=("note_id", "resource_id"),
            replace=True,
        )


def save_resource(db, resource):
    assert resource.find("data").attrib["encoding"] == "base64"
    if resource.find("data").text is None:
        return
    data = base64.b64decode(resource.find("data").text)
    md5 = hashlib.md5(data).hexdigest()
    row = {
        "md5": md5,
    }
    for tag in ("mime", "width", "height", "duration"):
        row[tag] = resource.find(tag).text if resource.find(tag) is not None else None
    attributes = resource.find("resource-attributes")
    if attributes is not None:
        row.update({attribute.tag: attribute.text for attribute in attributes})
    if resource.find("recognition") is not None:
        # Take the first <t> element in each <item> group
        words = []
        for item in ET.fromstring(resource.find("recognition").text).findall(".//item"):
            words.append(item.find("t").text)
        ocr = " ".join(words)
    else:
        ocr = None
    row["ocr"] = ocr
    db["resources"].insert(row, pk="md5", alter=True, replace=True)
    db["resources_data"].insert({"md5": md5, "data": data}, pk="md5", replace=True)
    return md5


def ensure_indexes(db):
    for column in ("created", "updated"):
        db["notes"].create_index([column], if_not_exists=True)
    if not db["notes_fts"].exists():
        db["notes"].enable_fts(
            ["title", "content"], create_triggers=True, tokenize="porter"
        )
    if not db["resources_fts"].exists():
        db["resources"].enable_fts(["ocr"], create_triggers=True, tokenize="porter")


def convert_datetime(s):
    return datetime.datetime.strptime(s, "%Y%m%dT%H%M%SZ").isoformat()
