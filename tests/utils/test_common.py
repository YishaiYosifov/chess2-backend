from collections import Counter
from typing import Sequence, Any


def get_duplicates(list: list[Any]):
    """Only get the duplicate items from a list"""

    counter = Counter(list)
    return [item for item, occurrences in counter.items() if occurrences >= 2]


class AsyncIterator:
    def __init__(self, messages: Sequence[Any]):
        self.iter = iter(messages)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration
