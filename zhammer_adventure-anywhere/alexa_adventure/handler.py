import os
import re
from typing import Any, Dict, Optional, cast

from adventure_anywhere.definitions import Config, Context
from adventure_anywhere.exceptions import CommandPolicyViolationError
from adventure_anywhere.game import GameEngine
from adventure_anywhere.s3_bucket_saves import S3BucketSavesGateway
from adventure_anywhere.use_adventure import do_command, last_output
from alexa_adventure.util import Skill

session_close_prompt = (
    "SAVING PROGRESS IN ADVENTURE. RESUME GAME BY SAYING 'ALEXA, OPEN CAVE ADVENTURE.'"
)


skill = Skill()
handle = skill.handle


@skill.intent("AMAZON.HelpIntent")
def _handle_help_request(event: Dict, context: Any) -> Dict:
    out = _replace_type_with_say(GameEngine.help_prompt())
    return _build_response(out, should_session_end=False)


@skill.intent("AMAZON.CancelIntent")
@skill.intent("AMAZON.StopIntent")
def _handle_stop_request(event: Dict, context: Any) -> Dict:
    return _build_response(session_close_prompt, should_session_end=True)


@skill.request("SessionEndedRequest")
def _handle_session_ended_request(event: Dict, context: Any) -> Dict:
    """
    >>> _handle_session_ended_request({"request":{"reason": "ERROR"}}, None)["response"]["outputSpeech"]["text"] #doctest: +ELLIPSIS
    "AN ERROR OCCURED. SAVING PROGRESS...ADVENTURE.'"
    >>> _handle_session_ended_request({"request":{"reason": "USER_INITIATED"}}, None)["response"]["outputSpeech"]["text"] #doctest: +ELLIPSIS
    "SAVING PROGRESS...ADVENTURE.'"
    """
    reason = event["request"]["reason"]
    prefix = "AN ERROR OCCURED. " if reason == "ERROR" else ""
    out = f"{prefix}{session_close_prompt}"
    return _build_response(out, should_session_end=True)


@skill.request("LaunchRequest")
def _handle_launch_request(event: Dict, context: Any) -> Dict:
    bucket_name = os.environ["SAVES_S3_BUCKET"]

    user_id = event["session"]["user"]["userId"]

    s3_bucket_saves = S3BucketSavesGateway(bucket_name)
    context = Context(saves=s3_bucket_saves)

    out = _replace_type_with_say(last_output(context, player_id=user_id))

    return _build_response(out, should_session_end=False)


@skill.intent("CommandIntent")
def _handle_command_intent_request(event: Dict, context: Any) -> Dict:
    bucket_name = os.environ["SAVES_S3_BUCKET"]

    user_id = event["session"]["user"]["userId"]

    command = _pluck_command(event)

    s3_bucket_saves = S3BucketSavesGateway(bucket_name)
    context = Context(saves=s3_bucket_saves)

    try:
        out = do_command(context, command, player_id=user_id)
    except CommandPolicyViolationError as e:
        out = str(e)

    return _build_response(_replace_type_with_say(out), should_session_end=False)


def _build_response(response_text: str, *, should_session_end: bool) -> Dict:
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"text": response_text, "type": "PlainText"},
            "shouldEndSession": should_session_end,
        },
    }


def _pluck_command(event: Dict) -> str:
    slots = event["request"]["intent"]["slots"]

    command_a: str = slots["commandA"]["value"]
    command_b: Optional[str] = slots.get("commandB", {}).get("value", None)

    return f"{command_a} {command_b}" if command_b else command_a


def _replace_type_with_say(text: str) -> str:
    """
    >>> _replace_type_with_say("TYPED")
    'TYPED'

    >>> _replace_type_with_say("TYPE")
    'SAY'

    >>> _replace_type_with_say("TYPE W RATHER THAN WEST")
    'SAY W RATHER THAN WEST'

    >>> _replace_type_with_say('WELCOME TO ADVENTURE!! WOULD YOU LIKE INSTRUCTIONS? - - - (TYPE "RESTART" TO RESTART THE GAME.)')  #doctest: +ELLIPSIS
    'WELCOME...SAY "RESTART"...'
    """
    return re.sub(r"\bTYPE\b", "SAY", text, flags=re.IGNORECASE)

