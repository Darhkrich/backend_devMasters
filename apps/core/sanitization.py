import re
import unicodedata

from django.utils.html import strip_tags


CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0B-\x1F\x7F]")
INLINE_WHITESPACE_PATTERN = re.compile(r"[^\S\r\n]+")
MULTI_BLANK_LINE_PATTERN = re.compile(r"\n{3,}")


def sanitize_text(value, *, multiline=False):
    if value is None:
        return value

    text = unicodedata.normalize("NFKC", str(value))
    text = CONTROL_CHARACTER_PATTERN.sub("", text)
    text = strip_tags(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if multiline:
        cleaned_lines = [INLINE_WHITESPACE_PATTERN.sub(" ", line).strip() for line in text.split("\n")]
        text = "\n".join(cleaned_lines)
        text = MULTI_BLANK_LINE_PATTERN.sub("\n\n", text)
        return text.strip()

    text = text.replace("\n", " ")
    text = INLINE_WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()


def sanitize_structure(value, *, multiline_fields=None, raw_fields=None, field_name=None):
    multiline_fields = multiline_fields or set()
    raw_fields = raw_fields or set()

    if field_name in raw_fields:
        return value

    if isinstance(value, str):
        return sanitize_text(value, multiline=field_name in multiline_fields)

    if isinstance(value, list):
        return [
            sanitize_structure(
                item,
                multiline_fields=multiline_fields,
                raw_fields=raw_fields,
                field_name=field_name,
            )
            for item in value
        ]

    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            clean_key = sanitize_text(key)
            sanitized[clean_key] = sanitize_structure(
                item,
                multiline_fields=multiline_fields,
                raw_fields=raw_fields,
                field_name=clean_key,
            )
        return sanitized

    return value
