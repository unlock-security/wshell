import re
from functools import reduce
from typing import Any, Dict, List, Mapping, Union


def _merge_dicts(a: Dict, b: Dict) -> Dict:
    for key, value in b.items():
        if key in a:
            if isinstance(a.get(key), dict) and isinstance(value, dict):
                _merge_dicts(a[key], value)
            elif isinstance(a.get(key), list) and isinstance(value, list):
                a[key].extend(value)
            else:
                a[key] = value
        else:
            a[key] = value
    return a


def _cast_value(value_str: str) -> Union[str, int, float, bool]:
    """
    Attempts to cast a string value to an appropriate type (int, float, bool).
    If the value is enclosed in single or double quotes, it's treated as a literal string.
    If no other casting is possible, the original string is returned.
    """
    if (value_str.startswith("'" ) and value_str.endswith("'" )) or \
       (value_str.startswith('"') and value_str.endswith('"')):
        return value_str[1:-1]

    if value_str.lower() == 'true':
        return True
    if value_str.lower() == 'false':
        return False

    try:
        return int(value_str)
    except ValueError:
        pass

    try:
        return float(value_str)
    except ValueError:
        pass

    return value_str


def _parse_key_value_pair(key_path: str, raw_value: str) -> Dict[str, Union[str, int, float, bool, List, Dict]]:
    """
    Parses a single key-value pair into a nested dictionary structure.

    It handles complex keys such as `key[nested_key][]`, transforming
    them into a corresponding nested dictionary or list structure.
    It also attempts to cast the value to its appropriate type (int, float, bool).
    """
    value = _cast_value(raw_value)

    base_key_match = re.match(r'^([^\[]+)', key_path)
    if not base_key_match:
        raise ValueError(f"Invalid key format: '{key_path}'. Key must start with a valid name.")

    base_key = base_key_match.group(1)
    sub_keys = re.findall(r'\[(.*?)\]', key_path)
    keys = [base_key] + sub_keys

    # Build the dictionary from the inside out for simplicity.
    result = value
    for key in reversed(keys):
        if key == '':
            # An empty key '[]' is a list.
            result = [result]
        else:
            # A named key '[name]' is a dictionary.
            result = {key: result}

    return result # pyright: ignore[reportReturnType]


def to_nested_dictionary(items: Mapping[str, str]) -> Dict[str, Any]:
    """
    Parses pairs of key-value items and merges them into a single,
    nested dictionary that represents the structured data.

    Args:
        items: A dictionary, where each string is a request item in the form
               `{"key_path[nested_key]": "value"}`.

    Returns:
        A dictionary containing the merged and structured data.
    """
    if not items:
        return {}

    parsed_item_dicts = [_parse_key_value_pair(key_path, raw_value) for key_path, raw_value in items.items()]
    return reduce(_merge_dicts, parsed_item_dicts, {})