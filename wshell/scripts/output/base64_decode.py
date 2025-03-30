import base64


def run(output: str) -> str:
    """Base64 decode output (requires --os to work)"""
    return base64.b64decode(output, validate=False).decode("utf-8", "ignore")