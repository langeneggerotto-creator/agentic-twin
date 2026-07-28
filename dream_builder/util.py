import json
import re


def extract_json_array(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in model output:\n{text}")
    return json.loads(match.group(0))
