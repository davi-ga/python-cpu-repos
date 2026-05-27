import re
from typing import Callable, Iterable, Optional


class command:
    @staticmethod
    def invalid_reason(command_text: str) -> Optional[str]:
        for policy in command._policies():
            violation = policy(command_text)
            if violation:
                return violation
        return None

    @staticmethod
    def _one_line_policy(command_text: str) -> Optional[str]:
        if "\n" in command_text:
            return "COMMAND CAN ONLY BE ONE LINE."
        return None

    @staticmethod
    def _prohibited_adventure_commands(command_text: str) -> Optional[str]:
        """
        >>> command._prohibited_adventure_commands("quit")
        '"QUIT" CANNOT BE USED IN SMS ADVENTURE.'
        >>> command._prohibited_adventure_commands(" quit")
        '"QUIT" CANNOT BE USED IN SMS ADVENTURE.'
        >>> command._prohibited_adventure_commands("quit game")
        '"QUIT" CANNOT BE USED IN SMS ADVENTURE.'
        >>> command._prohibited_adventure_commands("take lamp") is None
        True
        """
        prohibited_adventure_commands = ["quit", "save", "score", "suspend", "pause"]
        for prohibited_adventure_command in prohibited_adventure_commands:
            if command_text.lstrip().startswith(prohibited_adventure_command):
                return f'"{prohibited_adventure_command.upper()}" CANNOT BE USED IN SMS ADVENTURE.'

        return None

    @staticmethod
    def _includes_words_policy(command_text: str) -> Optional[str]:
        if not re.findall(r"\w+", command_text):
            return "COMMAND MUST CONTAIN AT LEAST ONE WORD."
        return None

    @staticmethod
    def _policies() -> Iterable[Callable[[str], Optional[str]]]:
        return (
            command._one_line_policy,
            command._includes_words_policy,
            command._prohibited_adventure_commands,
        )
