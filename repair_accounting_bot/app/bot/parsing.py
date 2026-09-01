def parse_staff_args(raw: str) -> tuple[int, str] | None:
    if '|' not in raw:
        return None
    left, right = [part.strip() for part in raw.split('|', 1)]
    if left.isdigit() and not right.isdigit():
        return int(left), right
    if right.isdigit() and not left.isdigit():
        return int(right), left
    if left.isdigit() and right.isdigit():
        return int(left), right
    return None
