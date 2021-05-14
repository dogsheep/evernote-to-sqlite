import re
from typing import Union, List, BinaryIO, Annotated, Tuple


def read_recovery_file(fn="/tmp/records.pickle") -> set:
    try:
        with open(fn, "rb") as f:
            records = pickle.load(f)
    except (FileNotFoundError, EOFError):
        records = set()
    return records


def update_recovery_file(records, fn="/tmp/records.pickle"):
    with open(fn, "wb") as f:
        pickle.dump(records, f)


class HugeXmlParser:
    def __init__(self, filename: str, tag: str = "note", max_size_mb: int = 30):
        """
        Class for handling big malformed XML files
        Args:
            filename: Input file
            tag:  The "root" tag you like to retrieve from the XML
            max_size_mb: The maximum size allowed once discovering the tag before carrying on to next
        """
        self.exceed_max = 0
        self.new_start = 0
        self.filename = filename
        self.tag = tag
        self.max_size_mb = max_size_mb

    @staticmethod
    def split_and_strip(whole_chunk: Union[str, bytes], tag: str = "note") -> List:
        """

        Args:
            whole_chunk: Input str or bytes
            tag: The tag to split upon

        Returns: List of chunk based on tag

        """
        if type(whole_chunk) is bytes:
            whole_chunk = whole_chunk.decode()
        chunks = re.split(fr"</?{tag}>", whole_chunk)
        chunks = [_ for _ in chunks if _.strip()]
        return chunks

    def split_multiple_tag_chunk(
        self, whole_chunk: Union[str, bytes], tag: str = "note"
    ) -> str:
        """
        Split and yield tags from str or bytes
        Args:
            whole_chunk: Input str or bytes
            tag: Tag to split out from whole_chunk

        Returns: yields str

        """
        chunks = self.split_and_strip(whole_chunk, tag)
        for chunk in chunks:
            yield "".join([f"<{tag}>", chunk, f"</{tag}>"])

    def escape_single_tag(self, whole_chunk, tag="content"):
        chunks = self.split_and_strip(whole_chunk, tag)
        if len(chunks) == 3:
            return "".join(
                [
                    chunks[0],
                    f"<{tag}>",
                    "<![CDATA[",
                    re.escape(chunks[1]),
                    "]]>",
                    f"</{tag}>",
                    chunks[2],
                ]
            )

    def tag_in_chunk(self, chunk: bytes) -> str:
        """
        Checks whether either start or end tag exists in tag used in class constructor.
        Args:
            chunk: The input bytes

        Returns:

        """
        if f"<{self.tag}>".encode() in chunk:
            return "start"
        if f"</{self.tag}>".encode() in chunk:
            return "end"

    @staticmethod
    def get_chunk_size(tag: str) -> int:
        """
        Return the number of bytes required to capture either start or end tag
        Args:
            tag: Tag to estimate size of

        Returns: Number of bytes

        """
        start, end = [f"<{tag}>", f"</{tag}>"]
        return max([len(_) for _ in (start, end)])

    def yield_tag(self, start_pos: int = 0) -> bytes:
        """
        Yield chunks of bytes covering the tag within the XML
        Args:
            start_pos: Instead of starting from beginning start the byte position

        Returns: Bytes including start and end tag

        """
        chunk_size = self.get_chunk_size(self.tag)
        index_content = 0
        with open(self.filename, "rb") as f:
            pos = start_pos
            while True:
                pos += 1
                f.seek(pos)
                chunk = f.read(chunk_size)
                if chunk == b"":
                    break
                if self.tag_in_chunk(chunk):
                    if self.tag_in_chunk(chunk) == "start":
                        index_content += 1
                        pos = yield from self.yield_content_until_end(
                            chunk,
                            chunk_size,
                            f,
                            index_content,
                            pos,
                        )

    def get_next_chunk_without_end(
        self, f: BinaryIO, pos: int, big_chunk: int = 1_000, margin: int = 10
    ) -> Tuple[int, Union[int, bytes]]:
        """
        Returns chunk of bytes that doesn't have a end-tag within the big_chunk size
        Args:
            f: File-pointer
            pos: Byte pointer
            big_chunk: Size in bytes to check
            margin: The margin at end excluded to avoid miss-match on end-tag

        Returns:

        """
        f.seek(pos)
        read_chunk_excluding_margin = f.read(big_chunk)[:-margin]
        if not self.tag_in_chunk(read_chunk_excluding_margin):
            pos += big_chunk - margin
            return pos, read_chunk_excluding_margin
        else:
            return pos, None

    def yield_content_until_end(
        self, chunk: bytes, chunk_size: int, f: BinaryIO, index_content: int, pos: int
    ) -> List[Annotated[int, "Start byte"], Annotated[int, "End byte"], bytes]:
        """
        Yields bytes until end tag reached
        Args:
            chunk: Current chunk
            chunk_size: Size in bytes to iterate
            f: Input file-pointer
            index_content: Current index number of content recovered
            pos: Current byte position

        Returns: List [start position, end position, bytes]

        """
        result = b""
        abort = False
        current_pos = 0
        last_megabyte_progress = 0
        start_pos = pos
        while self.tag_in_chunk(chunk) != "end":
            pos += 1
            # break if no data left
            if f.read(1) == "":
                break
            # get next big chunks without end-tag
            while True:
                pos, big_chunk_with_no_end = self.get_next_chunk_without_end(f, pos)
                # print(f"pos: {pos}, big_chunk_with_no_end: {big_chunk_with_no_end}")
                if big_chunk_with_no_end:
                    result += big_chunk_with_no_end
                    current_pos += len(big_chunk_with_no_end)
                    new_megabyte_progress = int(round(current_pos, -6) / 1_000_000)
                    if new_megabyte_progress is not last_megabyte_progress:
                        print(
                            f"processing current content {index_content}: {new_megabyte_progress} MB"
                        )
                        last_megabyte_progress = new_megabyte_progress
                else:
                    break
                if last_megabyte_progress >= self.max_size_mb:
                    print(f"Exceeding max size of {self.max_size_mb}, breaking")
                    self.exceed_max += 1
                    abort = True
                    break
            # carry on byte per byte now when end tag discovered
            f.seek(pos)
            result += f.read(1)
            chunk = f.read(chunk_size)
            if (
                self.tag_in_chunk(chunk) == "start"
                and f"</{self.tag}>" not in result.decode()
            ):
                print("Found new start, ending previous")
                end_tag = f"</{self.tag}>".encode()
                yield start_pos, pos + len(end_tag), result + end_tag
                pos -= 1
                abort = True
                self.new_start += 1
                break
            if abort:
                break
        if not abort:
            # Return start, end and chunk
            yield start_pos + 1, pos + len(chunk) + 1, result + chunk
        return pos
