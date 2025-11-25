def run(command: str) -> str:
    """ HTML encode in hexadecimal (using code points) all characters (e.g. ' -> &#x31;) """
    return ''.join("&#x%s;" % format(ord(c), "x") for c in command)