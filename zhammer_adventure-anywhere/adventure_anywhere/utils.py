import textwrap
from functools import reduce
from itertools import chain
from typing import Callable, Iterable, TypeVar

from adventure_anywhere.definitions import Notice

T = TypeVar("T")


def pipe(value: T, funcs: Iterable[Callable[[T], T]]) -> T:
    """
    >>> uppercase = lambda v: v.upper()
    >>> first_word = lambda v: v.split()[0]
    >>> pipe('hello world', [uppercase, first_word])
    'HELLO'
    """
    return reduce(lambda arg, func: func(arg), funcs, value)


def without_none_values(values: Iterable) -> Iterable:
    """
    >>> list(without_none_values(['a', 0, False, None, 25]))
    ['a', 0, False, 25]
    """
    return filter(lambda value: value is not None, values)


def with_delimiter(values: Iterable[T], delimiter: T) -> Iterable[T]:
    """
    >>> list(with_delimiter([], 'delim'))
    []

    >>> list(with_delimiter(['1'], 'delim'))
    ['1']

    >>> list(with_delimiter(['1', '2'], 'delim'))
    ['1', 'delim', '2']
    """
    is_first = True
    for value in values:
        if not is_first:
            yield delimiter
        is_first = False

        yield value


def notice(notice_text: str) -> Notice:
    return Notice(textwrap.fill(notice_text))
