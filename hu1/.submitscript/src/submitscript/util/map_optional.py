def map_optional(optional, f):
    return None if optional is None else f(optional)
