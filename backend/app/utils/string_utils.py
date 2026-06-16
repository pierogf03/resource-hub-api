def normalize_name(value: str) -> str:
    return value.strip()


def names_match(name_a: str, name_b: str) -> bool:
    return normalize_name(name_a).lower() == normalize_name(name_b).lower()
