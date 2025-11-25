def run(command: str) -> str:
    """ Slash escape single and double quotes (e.g. ' -> \') """
    return command.replace("'", "\\'").replace('"', '\\"')
