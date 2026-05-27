import json
import base64
import hashlib
import boto3
import pandas as pd
from os import environ
from boto3.dynamodb.conditions import Key
from src.scripts.io_s3 import s3_download, s3_upload
from src.pipelines.pipelines import load_highlight_analysis
from src.functions.analytics_save import check_pred_result

ddb_resource = boto3.resource("dynamodb")
ddb_table = ddb_resource.Table(environ.get("TABLE"))
shub_table = ddb_resource.Table(environ.get("TABLE_SHUB"))
s3_client = boto3.client("s3")
s3_bucket = environ.get("ARTIFACT_BUCKET")
skipped_fixtures = []

def handler(event, context):
  for record in event["Records"]:
    msg_body = record["body"]
    payload = json.loads(base64.b64decode(msg_body))
    payload_action = payload["action"]

    if payload_action == "UPDATE":
      update_item = compose_item(payload, payload_action)
      update_shub_ftscore(update_item)
      ft_score = update_item["ft_score"]
      fixture_id = update_item["fixture_id"]

      if ft_score != "-":
        prediction_status = get_pred_status(ft_score, fixture_id)
        if prediction_status:
          update_item.update({
            "prediction_status": prediction_status,
            "pred_status": prediction_status.split("#")[2]
          })
          update_pred_status(update_item)
      return True

    elif payload_action == "ADD":
      try:
        add_item = compose_item(payload, payload_action)
        shub_table.put_item(Item=add_item)
        print(f"Added fixture '{add_item['fixture_id']}' to shub table!")
        return True
      except Exception as error:
        raise Exception(f"Error adding item to scrapinghub table: {error}")

def get_pred_status(ft_score, fixture_id):
  try:
    ddb_result = ddb_table.query(
      KeyConditionExpression=Key("fixture_id").eq(fixture_id),
      ProjectionExpression="prediction_status"
    )

    old_prediction_status = ddb_result["Items"][0]["prediction_status"]
    highlight_pick = old_prediction_status.split("#")[0]
    prediction_pick = old_prediction_status.split("#")[1]

    pred_result = check_pred_result(ft_score, prediction_pick)
    prediction_status = f"{highlight_pick}#{prediction_pick}#{pred_result}"
    return prediction_status
  except IndexError:
    skipped_fixtures.append(fixture_id)
    return False
  except Exception as error:
    raise Exception(f"Error getting prediction status: {error}")

def update_pred_status(item):
  try:
    ddb_table.update_item(
      Key={ "fixture_id": item["fixture_id"] },
      UpdateExpression="set ft_score = :fts, prediction_status = :status_full, pred_status = :status_pred",
      ExpressionAttributeValues={
        ":fts": item["ft_score"],
        ":status_full": item["prediction_status"],
        ":status_pred": item["pred_status"]
      },
      ReturnValues="UPDATED_NEW"
    )
    print(f"Updated prediction status on '{item['fixture_id']}' successfully!")
  except Exception as error:
    raise Exception(f"Error updating prediction status on item: {error}")

def update_shub_ftscore(item):
  try:
    shub_table.update_item(
      Key={
        "fixture_id": item["fixture_id"],
      },
      UpdateExpression="set ft_score = :fts",
      ExpressionAttributeValues={
        ":fts": item["ft_score"]
      },
      ReturnValues="UPDATED_NEW"
    )
    print(f"Updated ftscore on '{item['fixture_id']}' successfully!")
  except Exception as error:
    raise Exception(f"Error updating ftscore on item: {error}")

def compose_item(item, action):
  if action == "UPDATE":
    update_item = {
      "fixture_id": item["fixture_id"],
      "ft_score": item["ft_score"]
    }
    return update_item

  elif action == "ADD":
    add_item = {
      "fixture_id": item["gameID"],
      # "expires_at": item["expires_at"],
      "ft_score": item["gameFtScore"],
      "play_date": item["gamePlayDate"],
      "play_time": item["gamePlayTime"],
      "home_team": item["gameHomeTeamName"],
      "away_team": item["gameAwayTeamName"],
      "league_url": item["leagueStatsUrl"],
      "league_name": item["leagueName"],
      "league_division_name": item["leagueDivisionName"]
    }
    return add_item
