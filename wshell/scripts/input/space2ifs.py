def run(command: str) -> str:
    """ Replaces space character (' ') with ${IFS} (Linux only) """
    return command.replace(" ", r"${IFS}")
