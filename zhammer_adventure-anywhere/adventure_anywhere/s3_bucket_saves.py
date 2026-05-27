import io
from typing import Optional

import boto3
import botocore

from adventure_anywhere.definitions import SavesGateway

s3 = boto3.resource("s3")


class S3BucketSavesGateway(SavesGateway):
    bucket_name: str

    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name

    def fetch_save(self, player_id: str) -> Optional[io.BytesIO]:
        s3_object = s3.Object(self.bucket_name, player_id)
        try:
            content = s3_object.get()
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise e

        return io.BytesIO(content["Body"].read())

    def update_save(self, player_id: str, save: io.BytesIO) -> None:
        s3_object = s3.Object(self.bucket_name, player_id)
        s3_object.put(Body=save.getvalue())
