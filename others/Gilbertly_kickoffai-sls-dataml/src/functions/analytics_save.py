import json
import boto3
import hashlib
import pandas as pd
from os import environ
from src.scripts.io_s3 import s3_download
from src.pipelines import analytics_column_names

s3_client = boto3.client("s3")
ddb_resource = boto3.resource("dynamodb")
ddb_table = environ.get("TABLE")
s3_bucket = environ.get("ARTIFACT_BUCKET")

def handler(event, context):
  bucket_path = event["bucket_path"]
  filename = bucket_path.split("/")[-1].split(".csv")[0]
  download_path = f"/tmp/{filename}.csv"

  s3_download(s3_client, s3_bucket, bucket_path, download_path)
  df = pd.read_csv(download_path, encoding="utf-8")

  for item in json.loads(df.to_json(orient="records")):
    save_to_dynamodb(compose_analytics_item(item))

  print("Successfully saved items to table!")
  return True

def save_to_dynamodb(item):
  try:
    ddb_table = ddb_resource.Table(environ.get("TABLE"))
    ddb_table.put_item(Item=item)
    return True
  except Exception as error:
    raise Exception(f"Error saving item: {error}")

def compose_analytics_item(item):
  def encode_string(value):
    return hashlib.sha1(
      value.encode("utf-8")
    ).hexdigest()

  play_date = item["gamePlayDate"]
  league_name = item["leagueName"]
  league_div_name = item["leagueDivisionName"]
  home_team = item["gameHomeTeamName"]
  away_team = item["gameAwayTeamName"]
  prediction_pick = item["slopeline_tip"]
  highlight_pick = item["highlight"]
  ft_score = item["gameFtScore"]
  pred_result = "PENDING"

  fixture_id = encode_string(
    play_date + home_team + away_team
  )

  if ft_score != "-":
    pred_result = check_pred_result(ft_score, highlight_pick)
    prediction_status = f"{highlight_pick}#{prediction_pick}#{pred_result}"
  else:
    prediction_status = f"{highlight_pick}#{prediction_pick}#{pred_result}"

  analytics_item = {
    "fixture_id": fixture_id, # partition key
    "play_date": play_date,
    "prediction_status": prediction_status,
    "pred_status": pred_result,
    "pred_pick": prediction_pick,
    "pred_highlight": highlight_pick,
    "play_time": item["gamePlayTime"],
    "home_team": home_team,
    "away_team": away_team,
    "league_name": league_name,
    "league_division_name": league_div_name,
    "ft_score": ft_score,
    "home_team_stats": {
      "position": str(item["HTS_teamPosition"]),
      "goal_difference": str(item["HTS_teamGoalsDifference"]),
      "ppg_total": str(item["HTS_teamPointsPerGame"]),
      "ppg_last_8": str(item["HTS_teamPPGlast8"]),
      "ppg_home": str(item["HTS_teamPPGHome"]),
      "ppg_away": str(item["HTS_teamPPGAway"]),
      "advantage_ppg_total": str(item["HTS_advantagePpg"]),
      "advantage_ppg_last_8": str(item["HTS_advantagePpgLast8"]),
      "advantage_ppg_home": str(item["HTS_advantagePpgHome"])
    },
    "away_team_stats": {
      "position": str(item["ATS_teamPosition"]),
      "goal_difference": str(item["ATS_teamGoalsDifference"]),
      "ppg_total": str(item["ATS_teamPointsPerGame"]),
      "ppg_last_8": str(item["ATS_teamPPGlast8"]),
      "ppg_home": str(item["ATS_teamPPGHome"]),
      "ppg_away": str(item["ATS_teamPPGAway"]),
      "advantage_ppg_total": str(item["ATS_advantagePpg"]),
      "advantage_ppg_last_8": str(item["ATS_advantagePpgLast8"]),
      "advantage_ppg_away": str(item["ATS_advantagePpgAway"])
    },
    "prediction_stats": {
      "model_one_home_draw": str(item["Predictions_1x"]),
      "model_one_home_away": str(item["Predictions_12"]),
      "model_one_away_draw": str(item["Predictions_x2"]),
      "model_one_slopeline": str(item["slopeline_1"]),
      "model_two_home_win": str(item["homeWin"]),
      "model_two_game_draw": str(item["awayWin"]),
      "model_two_away_win": str(item["gameDraw"]),
      "model_two_home_draw": str(item["homeDraw"]),
      "model_two_away_draw": str(item["awayDraw"]),
      "model_two_home_away": str(item["homeAway"]),
      "model_two_slopeline": str(item["slopeline_2"])
    }
  }
  return analytics_item

def check_pred_result(ft_score, prediction_pick):
  try:
    home_score = ft_score.split("-")[0]
    away_score = ft_score.split("-")[1]
    pred_result = "PENDING"
  except IndexError:
    pred_result = "PP"
    return pred_result

  if prediction_pick == "1x":
    if home_score >= away_score:
      pred_result = "WON"
    else:
      pred_result = "LOST"

  elif prediction_pick == "x2":
    if home_score <= away_score:
      pred_result = "WON"
    else:
      pred_result = "LOST"

  elif prediction_pick == "12":
    if home_score != away_score:
      pred_result = "WON"
    else:
      pred_result = "LOST"

  return pred_result
