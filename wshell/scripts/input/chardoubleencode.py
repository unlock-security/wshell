def run(command: str) -> str:
    """ Double URL-encodes each character in the payload (e.g. whoami -> %2577%2568%256f%2561%256d%2569) """
    return "".join(f"%25{format(ord(c), "x")}" for c in command)
