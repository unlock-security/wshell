def run(output: str) -> str:
    """ Unescape output (e.g. replace \\r and \\n with newlines) """
    return output.encode("latin-1", "backslashreplace").decode("unicode-escape")
