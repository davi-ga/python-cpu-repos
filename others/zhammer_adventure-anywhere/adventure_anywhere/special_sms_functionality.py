import textwrap
from functools import reduce
from typing import Optional

from adventure_anywhere.definitions import Config
from adventure_anywhere.utils import notice, pipe, with_delimiter, without_none_values

line_delimiter = "                             - - -"

restart_notice = notice('(TYPE "RESTART" AT ANY POINT TO RESTART THE GAME.)')


def add_after_start_notices(start_text: str, config: Config) -> str:
    after_start_notices = without_none_values(
        [start_text.rstrip("\n"), restart_notice, config.after_start_notice]
    )
    after_start_notices_with_line_delimiter = with_delimiter(
        after_start_notices, line_delimiter
    )
    return "\n".join(after_start_notices_with_line_delimiter)


def preprocess_command(command_text: str, config: Config) -> str:
    """
    >>> preprocess_command("game help", config=Config())
    'game help'
    >>> preprocess_command("take LAMP", config=Config())
    'take lamp'
    >>> preprocess_command("east", config=Config())
    'east'

    >>> import re
    >>> config = Config(preprocess_command=lambda command: re.sub(r'^game ', '', command))
    >>> preprocess_command("game help", config)
    'help'
    >>> preprocess_command("game HELP", config)
    'help'
    >>> preprocess_command("take LAMP", config)
    'take lamp'
    """
    processors = without_none_values([_lower, config.preprocess_command])
    return pipe(command_text, processors)


def _lower(string: str) -> str:
    return string.lower()


def is_restart_command(command_text: str) -> bool:
    """
    >>> is_restart_command("restart")
    True
    >>> is_restart_command("restart game")
    True
    >>> is_restart_command("take lamp")
    False
    """
    return command_text.startswith("restart")
