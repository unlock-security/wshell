from html import unescape


def run(output: str) -> str:
    """Unescapes HTML/XML entities in the output (e.g. &lt; in <)"""
    return unescape(output)