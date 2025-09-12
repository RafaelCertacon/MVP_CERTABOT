def _none_if_empty_str(v):
    return None if isinstance(v, str) and v.strip() == "" else v
