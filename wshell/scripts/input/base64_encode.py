import base64


def run(command: str) -> str:
    """ Base64 encode command """
    return base64.b64encode(command.encode("utf-8")).decode("utf-8")
