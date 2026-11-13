import sys
from datetime import datetime, timedelta, timezone


def _to_timestamp_ms(value, name):
    """Convert an unambiguous time bound to integer epoch milliseconds."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.utcoffset() is None:
            raise ValueError("%s must be a timezone-aware datetime" % name)
        return (value - datetime(1970, 1, 1, tzinfo=timezone.utc)) // timedelta(milliseconds=1)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise TypeError("%s must be an integer epoch millisecond timestamp or a timezone-aware datetime" % name)


if sys.version_info >= (3, 0):
    import urllib.parse
    dku_quote_fn = urllib.parse.quote
else:
    import urllib
    dku_quote_fn = urllib.quote


def _format_list(items, as_type):
    """Return list items or their resource handles, accepting singular aliases."""
    if as_type in ("listitems", "listitem"):
        return items
    if as_type in ("objects", "object"):
        return [item._to_object() for item in items]
    raise ValueError("Unknown as_type: %r" % (as_type,))
