def run(command: str) -> str:
    """ Replaces space character (' ') with comments '/**/' """
    return command.replace(" ", "/**/")
