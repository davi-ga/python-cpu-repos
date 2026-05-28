import boto3
from datetime import datetime, timedelta
from os import environ
from src.functions.csv_dump import send_sql

rds_client = boto3.client("rds-data")
ddb_resource = boto3.resource("dynamodb")
shub_table = ddb_resource.Table(environ.get("TABLE_SHUB"))
shub_index = environ.get("SHUB_INDEX")
db_name = environ.get("DB_NAME")
db_table = environ.get("DB_TABLE")
db_cluster_arn = environ.get("DB_CLUSTER_ARN")
db_secret_arn = environ.get("DB_SECRET_ARN")
pipeline_version = environ.get("PIPELINE_VERSION")

def handler(event, context):
  days_ago = []
  for day in range(1,8):
    date = (datetime.now() - timedelta(day)).strftime("%Y-%m-%d")
    days_ago.append(date)

  print(f"Offloading fixtures from '{days_ago[-1]}' to '{days_ago[0]}'")

  for day in days_ago:
    fixtures = get_day_fixtures(day)
    print(f"Updating '{len(fixtures)}' fixtures on '{day}' into aurora ...")

    for fixture in fixtures:
      update_sql = f"update {db_table} set gameFtScore = :fts where gameID = :id"
      update_params = [
        {"name": "id", "value":{"stringValue": fixture["fixture_id"]}},
        {"name": "fts", "value":{"stringValue": fixture["ft_score"]}}
      ]
      response = send_sql(db_name, db_secret_arn, db_cluster_arn, update_sql, update_params)
      if response:
        print(f"Updated '{day}' fixture id: '{fixture['fixture_id']}'")
  return {
    "query_dates": days_ago,
    "pipeline_version": pipeline_version
  }

def get_day_fixtures(date):
  day_fixtures = shub_table.query(
    IndexName=shub_index,
    KeyConditionExpression="play_date = :date and ft_score > :fts",
    ExpressionAttributeValues={ ":date": date, ":fts": "-" },
    ProjectionExpression="fixture_id, ft_score"
  )
  return day_fixtures["Items"]
