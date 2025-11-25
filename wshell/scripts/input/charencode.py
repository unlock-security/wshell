def run(command: str) -> str:
    """ URL-encodes all characters in a given command (e.g. whoami -> %77%68%6f%61%6d%69) """
    return "".join(f"%{format(ord(c), "x")}" for c in command)
