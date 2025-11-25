import base64


def run(command: str) -> str:
    """ Encodes the entire command using Base64 """
    return base64.b64encode(command.encode("utf-8")).decode("utf-8")
