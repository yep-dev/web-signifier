from datetime import datetime
from html import unescape
from html2text import HTML2Text


class PostlightFormat:
    formatter = {}

    def __init__(self, f):
        key, _ = f.__name__.rsplit("_", 1)
        self.formatter.update({key: f})
        self.format = f

    def __call__(self):
        self.format()


def format_date(obj):
    date = obj.get("date_published")
    if date is not None:
        obj["date_published"] = datetime.strptime(
            obj["date_published"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )


@PostlightFormat
def txt_format(obj):
    return obj["content"].get("text", "")


def postlight_main(result, body_width):
    text = HTML2Text()
    text.body_width = body_width
    text.ignore_emphasis = True
    text.ignore_images = True
    text.ignore_links = True
    text.convert_charrefs = True
    text.ul_item_mark = "-"
    result["content"] = {
        "html": result["content"],
        "text": unescape(text.handle(result["content"])),
    }
    return result
