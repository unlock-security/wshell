import re


def run(command: str) -> str:
    """ HTML encode (using code points) all non-alphanumeric characters (e.g. ' -> &#39;) """

    command = re.sub(r"&#(\d+);", lambda match: chr(int(match.group(1))), command)
    command = re.sub(r"[^\w]", lambda match: "&#%d;" % ord(match.group(0)), command)

    return command