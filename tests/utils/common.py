from collections import Counter
from typing import Any


def get_duplicates(list: list[Any]):
    """Only get the duplicate items from a list"""

    counter = Counter(list)
    return [item for item, occurrences in counter.items() if occurrences >= 2]
