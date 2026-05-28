import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from src.pipelines.transform_training import TeamPositionTransformer, BucketizeTransformer, \
  GamesPlayedTransformer, CleanSheetsTransformer, FtScoresTransformer
from src.pipelines.transform_inference import InferenceTransformer, HighlightAnalysisTransformer
from src.pipelines import db_column_names


class DataPreparationPipeline:
  """Prepare data in a way the model would understand."""
  def __init__(self):
    pass

  def pipeline_team_position(self):
    """Transform team position columns."""
    print("Transforming 'team_position' ...")
    cols_team_position = ["gamePosAdvantage"]
    bins_team_potision = [
      -30,-20,-15,-10,-8,-6,-2,0,2,6,8,10,15,20,30
    ]

    return [
      ("transform_team_position", TeamPositionTransformer()),
      ("bucketize_team_position", BucketizeTransformer(cols_team_position, bins_team_potision, single_col=True))
    ]

  def pipeline_games_played(self):
    """Transform games played columns."""
    print("Transforming 'games_played' ...")
    cols_games_won = ["teamGamesWon"]
    bins_games_won = [-1,5,10,15,20,25,30,35,40,45,50,55,60,65,100]

    cols_games_draw = ["teamGamesDraw"]
    bins_games_draw = [-1,5,10,15,20,25,30,35,40,45,100]

    cols_games_lost = ["teamGamesLost"]
    bins_games_lost = [-1,5,10,15,20,25,30,35,40,45,50,55,60,65,100]

    return [
      ("transform_games_played", GamesPlayedTransformer()),
      ("bucketize_games_won", BucketizeTransformer(cols_games_won, bins_games_won)),
      ("bucketize_games_draw", BucketizeTransformer(cols_games_draw, bins_games_draw)),
      ("bucketize_games_lost", BucketizeTransformer(cols_games_lost, bins_games_lost))
    ]

  def pipeline_goal_differences(self):
    """Transform goal differences columns."""
    print("Transforming 'goal_differences' ...")
    cols_goal_differences = ["teamGoalsDifference"]
    bins_goal_differences = [
      -90,-20,-18,-16,-14,-12,-10,-8,-6,-4,-2,0,2,4,6,8,10,12,14,16,18,20,90
    ]

    return [
      ("bucketize_goal_differences", BucketizeTransformer(cols_goal_differences, bins_goal_differences))
    ]

  def pipeline_points_per_game(self):
    """Transform points per game columns."""
    print("Transforming 'points_per_game' ...")
    cols_ppg = ["teamPointsPerGame"]
    bins_ppg = [-1,0.6,0.8,1.0,1.2,1.4,1.6,1.8,2.0,2.5,3.0]

    cols_ppg_last_8 = ["teamPPGlast8"]
    bins_ppg_last_8 = [-1,0.4,0.6,0.8,1.0,1.2,1.4,1.6,1.8,2.0,2.2,2.4,3.0]

    cols_ppg_home = ["teamPPGHome"]
    bins_ppg_home = [-1,0.2,0.4,0.6,0.8,1.0,1.2,1.4,1.6,1.8,2.0,2.2,2.4,2.6,2.8,3.0]

    cols_ppg_away = ["teamPPGAway"]
    bins_ppg_away = [-1,0.2,0.4,0.6,0.8,1.0,1.2,1.4,1.6,1.8,2.0,2.4,3.0]

    return [
      ("bucketize_ppg", BucketizeTransformer(cols_ppg, bins_ppg)),
      ("bucketize_ppg_last_8", BucketizeTransformer(cols_ppg_last_8, bins_ppg_last_8)),
      ("bucketize_ppg_home", BucketizeTransformer(cols_ppg_home, bins_ppg_home)),
      ("bucketize_ppg_away", BucketizeTransformer(cols_ppg_away, bins_ppg_away))
    ]

  def pipeline_cleansheets(self):
    """Transform cleansheets columns."""
    print("Transforming 'cleansheets' ...")
    cols_cleansheets = ["teamCleanSheetPercent"]
    bins_cleansheets = [
      -1,5,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,55,60,70,100
    ]

    return [
      ("transform_cleansheets", CleanSheetsTransformer()),
      ("bucketize_cleansheets", BucketizeTransformer(cols_cleansheets, bins_cleansheets))
    ]

  def pipeline_goals_scored(self):
    """Transform goals scored columns."""
    print("Transforming 'goals_scored' ...")
    cols_home_goals_scored = ["homeGoalsScored"]
    bins_home_goals_scored = [-1,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,40,80]

    cols_away_goals_scored = ["awayGoalsScored"]
    bins_away_goals_scored = [-1,2,4,6,8,10,12,14,16,18,20,22,24,26,80]

    cols_home_goals_conceded = ["homeGoalsConcededPerMatch"]
    bins_home_goals_conceded = [-1,0.2,0.4,0.6,0.8,1.0,1.2,1.4,1.6,1.8,2,3,15]

    cols_home_goals_scored_conceded = ["homeScored_ConcededPerMatch"]
    bins_home_goals_scored_conceded = [-1,1,1.4,1.6,1.8,2,2.2,2.4,2.6,2.8,3.0,3.2,3.4,3.6,3.8,4,15]

    cols_away_goals_conceded = ["awayGoalsConcededPerMatch"]
    bins_away_goals_conceded = [-1,0.4,0.6,0.8,1,1.2,1.4,1.6,1.8,2.0,2.2,2.4,2.6,3,15]

    cols_away_goals_scored_conceded = ["awayScored_ConcededPerMatch"]
    bins_away_goals_scored_conceded = [-1,1.2,1.4,1.6,1.8,2,2.2,2.4,2.6,2.8,3,3.2,3.4,3.6,3.8,4,5,15]

    return [
      ("bucketize_home_goals_scored", BucketizeTransformer(cols_home_goals_scored, bins_home_goals_scored)),
      ("bucketize_away_goals_scored", BucketizeTransformer(cols_away_goals_scored, bins_away_goals_scored)),
      ("bucketize_home_goals_conceded", BucketizeTransformer(cols_home_goals_conceded, bins_home_goals_conceded)),
      ("bucketize_home_goals_scored_conceded", BucketizeTransformer(cols_home_goals_scored_conceded, bins_home_goals_scored_conceded)),
      ("bucketize_away_goals_conceded", BucketizeTransformer(cols_away_goals_conceded, bins_away_goals_conceded)),
      ("bucketize_away_goals_scored_conceded", BucketizeTransformer(cols_away_goals_scored_conceded, bins_away_goals_scored_conceded))
    ]

  def pipeline_ftscores(self, csv_label=None):
    """Transform ft scores columns."""
    return [
      ("transform_ftscores", FtScoresTransformer(csv_label))
    ]

  def fit_pipeline(self, df, csv_label=None):
    """Compose pipeline to transform desired columns."""
    print("Fitting pipeline ...")
    pipeline = Pipeline(
      self.pipeline_ftscores(csv_label) +
      self.pipeline_team_position() + self.pipeline_games_played() +
      self.pipeline_goal_differences() + self.pipeline_points_per_game() +
      self.pipeline_cleansheets() + self.pipeline_goals_scored()
    )

    df = pipeline.fit_transform(df)
    print("Fitted pipeline successfully!")

    categorical_cols = df.select_dtypes(["category"]).columns
    df[categorical_cols] = df[categorical_cols].apply(lambda row: row.cat.codes)

    return df


class InferenceAnalysisPipeline:
  """Transform and analyze data the model returned as inference."""
  def __init__(self):
    pass

  def fit_pipeline(self, df, pre_analysis=True, algorithm="v1"):
    """Compose an inference-analysis pipeline."""
    if pre_analysis:
      df = df.drop(["gameID", "gameHomeTeamID", "gameAwayTeamID"], axis=1)
    else:
      df = df[df.gameFtScore != "-"]
      df = df.drop(["gameID", "gamePlayTime", "gameHomeTeamID", "gameAwayTeamID"], axis=1)

    total_rows = df.shape[0]
    print(f"Loaded dataframe with {total_rows} rows.")

    pipeline = Pipeline([
      ("transform_inference", InferenceTransformer(pre_analysis, algorithm))
    ])
    df = pipeline.fit_transform(df)
    print("Fitted pipeline successfully!")
    return df, total_rows


class HighlightAnalysisPipeline:
  def __init__(self):
    pass

  def fit_pipeline(self, df):
    """Compose a highlight-analysis pipeline."""
    pipeline = Pipeline([
      ("highlight_analysis", HighlightAnalysisTransformer())
    ])
    df = pipeline.fit_transform(df)
    print("Fitted pipeline successfully!")
    return df


def load_pipeline_v1(pipeline_type, csv_filename, csv_label):
  """Prepare data for training or inference with version 1 of the pipeline."""
  df_columns = [
    "gameFtScore",
    "HTS_teamPosition", "HTS_teamGamesPlayed", "HTS_teamGamesWon",
    "HTS_teamGamesDraw", "HTS_teamGamesLost", "HTS_teamGoalsDifference",
    "HTS_teamPointsPerGame", "HTS_teamPPGlast8", "HTS_teamCleanSheetPercent",
    "HTS_teamPPGHome", "HTS_teamPPGAway", "HTS_homeGoalsScored", "HTS_awayGoalsScored",
    "HTS_homeGoalsConcededPerMatch", "HTS_homeScored_ConcededPerMatch",
    "HTS_awayGoalsConcededPerMatch", "HTS_awayScored_ConcededPerMatch",
    "ATS_teamPosition", "ATS_teamGamesPlayed", "ATS_teamGamesWon",
    "ATS_teamGamesDraw", "ATS_teamGamesLost", "ATS_teamGoalsDifference",
    "ATS_teamPointsPerGame", "ATS_teamPPGlast8", "ATS_teamCleanSheetPercent",
    "ATS_teamPPGHome", "ATS_teamPPGAway", "ATS_homeGoalsScored", "ATS_awayGoalsScored",
    "ATS_homeGoalsConcededPerMatch", "ATS_homeScored_ConcededPerMatch",
    "ATS_awayGoalsConcededPerMatch", "ATS_awayScored_ConcededPerMatch"
  ]

  df = pd.read_csv(csv_filename, header=0, names=db_column_names, usecols=df_columns, na_values="None", encoding="utf-8")
  if pipeline_type == "train":
    df.loc[df['gameFtScore'] == '-', 'gameFtScore'] = np.nan
    df.dropna(inplace=True)
    print(f"Loading '{csv_filename}' into 'pv1' train pipeline ...")

    df = DataPreparationPipeline().fit_pipeline(df, csv_label)
    train_df, validation_df = split_train_test(df)

    if csv_label == "xc":
      validation_df = validation_df.drop(validation_df.columns[1], axis=1)

    train_filename = csv_filename.split(".csv")[0] + "_train_pv1.csv"
    validation_filename = csv_filename.split(".csv")[0] + "_validation_pv1.csv"

    df_to_csv(train_df, train_filename)
    df_to_csv(validation_df, validation_filename)
    print(f"Successfully transformed 'pv1' train pipeline!")
    return train_filename, validation_filename

  elif pipeline_type == "inference":
    print(f"Loading '{csv_filename}' into 'pv1' inference pipeline ...")
    df = DataPreparationPipeline().fit_pipeline(df)
    df.dropna(inplace=True)

    inference_filename = csv_filename.split(".csv")[0] + "_inference_pv1.csv"
    df_to_csv(df, inference_filename)
    print(f"Successfully transformed 'pv1' inference pipeline!")
    return inference_filename

def load_inference_pipeline_v1(csv_filename, pre_analysis=True, algorithm="v1"):
  """Prepare inference data for analysis with version 1 of the pipeline."""
  df = pd.read_csv(csv_filename, encoding="utf-8")
  print(f"Loading '{csv_filename}' into 'pv1' inference-analysis pipeline ...")

  df, total_rows = InferenceAnalysisPipeline().fit_pipeline(df, pre_analysis, algorithm)
  print(f"Successfully transformed 'pv1' inference-analysis pipeline!")

  analysis_filename = csv_filename.split(".csv")[0] + "_analysis_pv1.csv"
  df_to_csv(df, analysis_filename, header=True)
  return analysis_filename

def load_highlight_analysis(csv_filename):
  """Highlight fixtures' attractiveness with transformer pipeline."""
  df = pd.read_csv(csv_filename, encoding="utf-8")
  print(f"Highlighting '{csv_filename}' ...")
  df = HighlightAnalysisPipeline().fit_pipeline(df)
  print("Successfully transformed analysis-highlight pipeline!")

  highlights_filename = csv_filename.split(".csv")[0] + "_highlights.csv"
  df_to_csv(df, highlights_filename, header=True)
  return highlights_filename

def concat_csv_stage_one(features_filepath, predictions_filepath, csv_label, multiclass=False):
  """Concat Sagemaker inference (predictions) with original data (features) into one csv."""
  df_columns = [
    "gameID", "gamePlayDate", "gamePlayTime", "gameHomeTeamName",
    "gameAwayTeamName", "leagueName", "leagueDivisionName",
    "HTS_teamPosition", "HTS_teamGoalsDifference",
    "ATS_teamPosition", "ATS_teamGoalsDifference",
    "HTS_teamPointsPerGame", "HTS_teamPPGlast8",
    "ATS_teamPointsPerGame", "ATS_teamPPGlast8",
    "HTS_teamPPGHome", "HTS_teamPPGAway",
    "ATS_teamPPGHome", "ATS_teamPPGAway",
    "gameHomeTeamID", "gameAwayTeamID",
    "gameFtScore"
  ]

  df_features = pd.read_csv(features_filepath, usecols=df_columns, encoding="utf-8")

  if not multiclass:
    df_predictions = pd.read_csv(
      predictions_filepath, sep=" ", names=[f"Predictions_{csv_label}"], encoding="utf-8"
    )
  else:
    multiclass_columns = ["homeWin", "awayWin", "gameDraw"]
    df_predictions = pd.read_csv(
      predictions_filepath, sep=",", names=multiclass_columns, encoding="utf-8"
    )

  print(f"Concatenating csv files '{features_filepath}' + '{predictions_filepath}' ...")
  df_concat = pd.concat([df_features, df_predictions], axis=1)
  filename = features_filepath.split("/")[-1]
  concat_csv_path = f"/tmp/concat_{csv_label}_{filename}"
  df_to_csv(df_concat, concat_csv_path, header=True)
  return concat_csv_path

def concat_csv_stage_two(csv_1x_path, csv_12_path, csv_x2_path, csv_xc_path):
  """Concat all models' csv predictions into one predictions' csv."""
  col_predictions_12 = "Predictions_12"
  col_predictions_x2 = "Predictions_x2"
  cols_predictions_xc = ["homeWin", "gameDraw", "awayWin"]

  df_1x = pd.read_csv(csv_1x_path, encoding="utf-8")
  # df_1x doesn't need usecols because we return all available columns; features + 1x predictions
  # For more reference check: concat_csv_stage_one()
  df_12 = pd.read_csv(csv_12_path, encoding="utf-8", usecols=[col_predictions_12])
  df_x2 = pd.read_csv(csv_x2_path, encoding="utf-8", usecols=[col_predictions_x2])
  df_xc = pd.read_csv(csv_xc_path, encoding="utf-8", usecols=cols_predictions_xc)

  print(f"Concatenating csv files: '{csv_1x_path}', '{csv_12_path}', '{csv_x2_path}', '{csv_xc_path}' ...")
  df_concat = pd.concat([df_1x, df_12, df_x2, df_xc], axis=1)

  filename = csv_1x_path.split("/")[-1].split("1x_")[-1]
  concat_csv_filepath = f"/tmp/concat_all_{filename}"
  df_to_csv(df_concat, concat_csv_filepath, header=True)
  return concat_csv_filepath

def split_train_test(df, random_state=42, test_size=0.2):
  targets = df["gameFtScore"]
  train, validation = train_test_split(
    df, random_state=random_state, test_size=test_size, stratify=targets
  )
  return train, validation

def df_to_csv(df, csv_filename, header=False):
  print(f"Converting dataframe to csv '{csv_filename}' ...")
  df.to_csv(csv_filename, sep=",", encoding="utf-8", index=False, header=header)
  print(f"Successfully saved dataframe to csv!")
