import os
import re
from typing import Any, Dict

from adventure_anywhere.definitions import Config, Context
from adventure_anywhere.exceptions import CommandPolicyViolationError
from adventure_anywhere.s3_bucket_saves import S3BucketSavesGateway
from adventure_anywhere.use_adventure import do_command
from adventure_anywhere.utils import notice

after_start_notice = notice(
    '(SOME OF THE ORIGINAL ADVENTURE COMMANDS LIKE "HELP" AND "INFO" '
    "ARE INTERCEPTED BY THE SMS TEXT MESSAGE PROVIDER BEFORE THEY CAN "
    'BE PROCESSED BY THE GAME. IF YOU RUN INTO THIS ISSUE, TYPE "GAME " '
    'BEFORE THE COMMAND, SUCH AS "GAME HELP" OR "GAME INFO".)'
)


def preprocess_command(command: str) -> str:
    return re.sub(r"^game ", "", command)


sms_config = Config(
    preprocess_command=preprocess_command, after_start_notice=after_start_notice
)


def handle_sms(event: Dict, context: Any) -> str:
    bucket_name = os.environ["SAVES_S3_BUCKET"]

    sms_number = event["body"]["From"]
    command = event["body"]["Body"].lower()

    s3_bucket_saves = S3BucketSavesGateway(bucket_name)
    context = Context(config=sms_config, saves=s3_bucket_saves)

    try:
        out = do_command(context, command, player_id=sms_number)
    except CommandPolicyViolationError as e:
        out = f"SMS ERROR: {str(e)}"

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{out}</Message></Response>"
    )
