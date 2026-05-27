#!/usr/bin/env python3
import pprint
import sys
from contextlib import contextmanager

import boto3
import psycopg2
from botocore.config import Config

DB_HOST = "sb-{environment}.cgrvtkkg9riu.us-east-2.rds.amazonaws.com"
ENVIRONMENT = "production"


def get_db_password():
    client = boto3.client("ssm", config=Config(region_name="us-east-2"))
    return client.get_parameter(
        Name=f"/{ENVIRONMENT}/db_password", WithDecryption=True
    )["Parameter"]["Value"]


def main():
    with psql_connection() as psql:
        solves(psql)

    return 0


@contextmanager
def psql_connection():
    psql = psycopg2.connect(
        dbname="scoreboard",
        host=DB_HOST.format(environment=ENVIRONMENT),
        password=get_db_password(),
        user="scoreboard",
    )
    try:
        yield psql
    finally:
        psql.close()


def solves(psql):
    with psql.cursor() as cursor:
        cursor.execute("SELECT * FROM solves;")
        result = cursor.fetchall()
        pprint.pprint(result)


if __name__ == "__main__":
    sys.exit(main())
