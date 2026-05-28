import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin


class InferenceTransformer(BaseEstimator, TransformerMixin):
  def __init__(self, pre_analysis=True, algorithm="v1"):
    self.pre_analysis = pre_analysis
    self.algorithm = algorithm

  def fit(self, X, y=None):
    return self

  def remove_square_brackets(self, X):
    X["homeWin"] = X["homeWin"].apply(
      lambda row: pd.Series(row.split("[")[1]).astype(float))

    X["awayWin"] = X["awayWin"].apply(
      lambda row: pd.Series(row).astype(float))

    X["gameDraw"] = X["gameDraw"].apply(
      lambda row: pd.Series(row.split("]")[0]).astype(float))
    return X

  def calculate_results(self, X):
    X["homeScore"] = X["gameFtScore"].apply(
      lambda row: row.split("-")[0]
    )
    X["awayScore"] = X["gameFtScore"].apply(
      lambda row: row.split("-")[1]
    )

    X["result"] = np.where(
      X["homeScore"] == X["awayScore"],
      "x",
      np.where(
        X["homeScore"] > X["awayScore"],
        "1x",
        np.where(
          X["homeScore"] < X["awayScore"],
          "x2", False
        )
      )
    )
    X = X.drop(["homeScore", "awayScore"], axis=1)
    return X

  def make_double_chance(self, X):
    X["homeDraw"] = X.apply(lambda row: row["homeWin"] + row["gameDraw"], axis=1)
    X["awayDraw"] = X.apply(lambda row: row["awayWin"] + row["gameDraw"], axis=1)
    X["homeAway"] = X.apply(lambda row: row["homeWin"] + row["awayWin"], axis=1)
    return X

  def make_slopelines(self, X):
    X["slopeline_1"] = np.where(
      np.logical_and(
        np.logical_and(
          X["Predictions_1x"] > X["Predictions_12"],
          X["Predictions_1x"] > X["Predictions_x2"]
        ), # Predictions_1x largest, Predictions_12 second largest
        X["Predictions_12"] > X["Predictions_x2"]
      ), "1x,12,x2", # 1st possible slopeline
      np.where(
        np.logical_and(
          np.logical_and(
            X["Predictions_1x"] > X["Predictions_12"],
            X["Predictions_1x"] > X["Predictions_x2"]
          ), # Predictions_1x largest, Predictions_x2 second largest
          X["Predictions_x2"] > X["Predictions_12"]
        ), "1x,x2,12", # 2nd possible slopeline
        np.where(
          np.logical_and(
            np.logical_and(
              X["Predictions_12"] > X["Predictions_1x"],
              X["Predictions_12"] > X["Predictions_x2"]
            ), # Predictions_12 largest, Predictions_1x second largest
            X["Predictions_1x"] > X["Predictions_x2"]
          ), "12,1x,x2", # 3rd possible slopeline
          np.where(
            np.logical_and(
              np.logical_and(
                X["Predictions_12"] > X["Predictions_1x"],
                X["Predictions_12"] > X["Predictions_x2"]
              ), # Predictions_12 largest, Predictions_x2 second largest
              X["Predictions_x2"] > X["Predictions_1x"]
            ), "12,x2,1x", # 4th possible slopeline
            np.where(
              np.logical_and(
                np.logical_and(
                  X["Predictions_x2"] > X["Predictions_1x"],
                  X["Predictions_x2"] > X["Predictions_12"]
                ), # Predictions_x2 largest, Predictions_1x second largest
                X["Predictions_1x"] > X["Predictions_12"]
              ), "x2,1x,12", # 5th possible slopeline
              np.where(
                np.logical_and(
                  np.logical_and(
                    X["Predictions_x2"] > X["Predictions_1x"],
                    X["Predictions_x2"] > X["Predictions_12"]
                  ), # Predictions_x2 largest, Predictions_12 second largest
                  X["Predictions_12"] > X["Predictions_1x"]
                ), "x2,12,1x", # 6th possible slopeline
                False
              )
            )
          )
        )
      )
    )

    X["slopeline_2"] = np.where(
      np.logical_and(
        np.logical_and(
          X["homeDraw"] > X["homeAway"],
          X["homeDraw"] > X["awayDraw"],
        ), # homeDraw is largest, homeAway is second-largest
        X["homeAway"] > X["awayDraw"]
      ), "1x,12,x2", # 1st possible slopeline
      np.where(
        np.logical_and(
          np.logical_and(
            X["homeAway"] > X["homeDraw"],
            X["homeAway"] > X["awayDraw"],
          ), # homeAway is largest, homeDraw is second-largest
          X["homeDraw"] > X["awayDraw"]
        ), "12,1x,x2", # 2nd possible slopeline
        np.where(
          np.logical_and(
            np.logical_and(
              X["homeDraw"] > X["homeAway"],
              X["homeDraw"] > X["awayDraw"],
            ), # homeDraw is largest, awayDraw is second-largest
            X["awayDraw"] > X["homeAway"]
          ), "1x,x2,12", # 3rd possible slopeline
          np.where(
            np.logical_and(
              np.logical_and(
                X["awayDraw"] > X["homeAway"],
                X["awayDraw"] > X["homeDraw"],
              ), # awayDraw is largest, homeAway is second-largest
              X["homeDraw"] > X["homeAway"]
            ), "x2,1x,12", # 4th possible slopeline
            np.where(
              np.logical_and(
                np.logical_and(
                  X["homeAway"] > X["homeDraw"],
                  X["homeAway"] > X["awayDraw"],
                ), # homeAway is largest, awayDraw is second-largest
                X["awayDraw"] > X["homeDraw"]
              ), "12,x2,1x", # 5th possible slopeline
              np.where(
                np.logical_and(
                  np.logical_and(
                    X["awayDraw"] > X["homeDraw"],
                    X["awayDraw"] > X["homeAway"],
                  ), # awayDraw is largest, homeAway is second-largest
                  X["homeAway"] > X["homeDraw"]
                ), "x2,12,1x", # 6th possible slopeline
                False
              )
            )
          )
        )
      )
    )
    return X

  def make_naive(self, X):
    X["naive_1"] = np.where(
      np.logical_and(
        X["Predictions_1x"] > X["Predictions_x2"],
        X["Predictions_1x"] > X["Predictions_12"],
      ), "1x",
      np.where(
        np.logical_and(
          X["Predictions_x2"] > X["Predictions_1x"],
          X["Predictions_x2"] > X["Predictions_12"],
        ), "x2",
        np.where(
          np.logical_and(
            X["Predictions_12"] > X["Predictions_1x"],
            X["Predictions_12"] > X["Predictions_x2"],
          ), "12", False
        )
      )
    )

    X["naive_2"] = np.where(
      np.logical_and(
        X["homeDraw"] > X["awayDraw"],
        X["homeDraw"] > X["homeAway"],
      ), "1x",
      np.where(
        np.logical_and(
          X["awayDraw"] > X["homeDraw"],
          X["awayDraw"] > X["homeAway"],
        ), "x2",
        np.where(
          np.logical_and(
            X["homeAway"] > X["homeDraw"],
            X["homeAway"] > X["awayDraw"],
          ), "12", False
        )
      )
    )

    X["naive_3"] = np.where(X["naive_1"] == X["naive_2"], X["naive_1"], "12")
    return X

  def make_ppg_advantages(self, X):
    X["HTS_advantagePpg"] = X.apply(
      lambda row: round(row["HTS_teamPointsPerGame"] - row["ATS_teamPointsPerGame"], 2),
      axis=1
    )
    X["HTS_advantagePpgLast8"] = X.apply(
      lambda row: round(row["HTS_teamPPGlast8"] - row["ATS_teamPPGlast8"], 2),
      axis=1
    )
    X["HTS_advantagePpgHome"] = X.apply(
      lambda row: round(row["HTS_teamPPGHome"] - row["ATS_teamPPGAway"], 2),
      axis=1
    )

    X["ATS_advantagePpg"] = X.apply(
      lambda row: round(row["ATS_teamPointsPerGame"] - row["HTS_teamPointsPerGame"], 2),
      axis=1
    )
    X["ATS_advantagePpgLast8"] = X.apply(
      lambda row: round(row["ATS_teamPPGlast8"] - row["HTS_teamPPGlast8"], 2),
      axis=1
    )
    X["ATS_advantagePpgAway"] = X.apply(
      lambda row: round(row["ATS_teamPPGAway"] - row["HTS_teamPPGHome"], 2),
      axis=1
    )
    return X

  def make_slopeline_tip(self, X):
    X["slopeline_1a"] = X["slopeline_1"].apply(lambda row: row.split(",")[0])
    X["slopeline_1b"] = X["slopeline_1"].apply(lambda row: row.split(",")[1])
    X["slopeline_1c"] = X["slopeline_1"].apply(lambda row: row.split(",")[2])

    X["slopeline_2a"] = X["slopeline_2"].apply(lambda row: row.split(",")[0])
    X["slopeline_2b"] = X["slopeline_2"].apply(lambda row: row.split(",")[1])
    X["slopeline_2c"] = X["slopeline_2"].apply(lambda row: row.split(",")[2])

    X["slopeline_tip"] = np.where(
      X["slopeline_1a"] == X["slopeline_2a"],
      X["slopeline_2a"],
      np.where(
        np.logical_or(
          np.logical_and(
            X["slopeline_1a"] == "1x",
            X["slopeline_2a"] == "x2"
          ),
          np.logical_and(
            X["slopeline_2a"] == "1x",
            X["slopeline_1a"] == "x2"
          )
        ), "12", # Case [1x,x2]
        np.where(
          np.logical_or(
            np.logical_and(
              X["slopeline_1a"] == "1x",
              X["slopeline_2a"] == "12"
            ),
            np.logical_and(
              X["slopeline_2a"] == "1x",
              X["slopeline_1a"] == "12"
            )
          ), "1x", # Case [1x,12]
          np.where(
            np.logical_or(
              np.logical_and(
                X["slopeline_1a"] == "x2",
                X["slopeline_2a"] == "1x"
              ),
              np.logical_and(
                X["slopeline_2a"] == "x2",
                X["slopeline_1a"] == "1x"
              ),
            ), "12", # Case [x2,1x]
            np.where(
              np.logical_or(
                np.logical_and(
                  X["slopeline_1a"] == "x2",
                  X["slopeline_2a"] == "12"
                ),
                np.logical_and(
                  X["slopeline_2a"] == "x2",
                  X["slopeline_1a"] == "12"
                )
              ), "x2", # Case [x2,12]
              np.where(
                np.logical_or(
                  np.logical_and(
                    X["slopeline_1a"] == "12",
                    X["slopeline_2a"] == "1x"
                  ),
                  np.logical_and(
                    X["slopeline_2a"] == "12",
                    X["slopeline_1a"] == "1x"
                  )
                ), "1x", # Case [12,1x]
                np.where(
                  np.logical_or(
                    np.logical_and(
                      X["slopeline_1a"] == "12",
                      X["slopeline_2a"] == "x2"
                    ),
                    np.logical_and(
                      X["slopeline_2a"] == "12",
                      X["slopeline_1a"] == "x2"
                    )
                  ), "x2", False # Case [12,x2]
                )
              )
            )
          )
        )
      )
    )

    X.drop([
      "slopeline_1a", "slopeline_1b", "slopeline_1c",
      "slopeline_2a", "slopeline_2b", "slopeline_2c"
    ], inplace=True, axis=1)
    return X

  def calculate_performance(self, X, columns):
    assert isinstance(columns, list)
    for col in columns:
      try:
        X[f"{col}_perf"] = np.where(
          X[col] == X["result"], "✅",
          np.where(
            np.logical_or(
              np.logical_and(
                X[col] == "12",
                X["result"] == "1x"
              ),
              np.logical_and(
                X[col] == "12",
                X["result"] == "x2"
              )
            ), "✅", # Case: [12,1x], [12,x2]
            np.where(
              np.logical_or(
                np.logical_and(
                  X[col] == "x",
                  X["result"] == "1x"
                ),
                np.logical_and(
                  X[col] == "x",
                  X["result"] == "x2"
                )
              ), "✅", # Case: [x,1x], [x,x2]
              np.where(
                np.logical_or(
                  np.logical_and(
                    X[col] == "1x",
                    X["result"] == "x"
                  ),
                  np.logical_and(
                    X[col] == "x2",
                    X["result"] == "x"
                  )
                ), "✅", "🔥" # Case: [1x,x], [x2,x]
              )
            )
          )
        )
      except Exception as error:
        raise Exception(f"Error calculating column '{col}' performance: {error}")
    return X

  def algorithm_v1(self, X):
    if self.pre_analysis:
      try:
        print("Fitting pre-game analysis dataframe (algorithm_v1) ...")
        X = self.remove_square_brackets(X)
        # X = self.calculate_results(X)
        X = self.make_double_chance(X)
        X = self.make_ppg_advantages(X)
        X = self.make_slopelines(X)
        # X = self.make_naive(X)
        X = self.make_slopeline_tip(X)
        # X = self.calculate_performance(X, [# "naive_1", "naive_2", "naive_3",
        #                                   "slopeline_tip"]
        # )
      except Exception as error:
        raise Exception(
          f"(algorithm_v1) Encountered error on pre-game transformer: '{error}'"
        )
    else:
      try:
        print("Fitting post-game analysis dataframe (algorithm_v1) ...")
        X = self.remove_square_brackets(X)
        X = self.calculate_results(X)
        X = self.make_double_chance(X)
        X = self.make_ppg_advantages(X)
        X = self.make_slopelines(X)
        # X = self.make_naive(X)
        X = self.make_slopeline_tip(X)
        X = self.calculate_performance(X, [# "naive_1", "naive_2", "naive_3",
                                          "slopeline_tip"]
        )
      except Exception as error:
        raise Exception(
          f"(algorithm_v1) Encountered error on post-game transformer: '{error}'"
        )
    return X

  def algorithm_v2(self, X):
    if self.pre_analysis:
      try:
        print("Fitting pre-game analysis dataframe (algorithm_v2) ...")
        X = self.remove_square_brackets(X)
        # X = self.calculate_results(X)
        X = self.make_double_chance(X)
        X = self.make_ppg_advantages(X)
        X = self.make_slopelines(X)
        # X = self.make_naive(X)
        X = self.make_slopeline_tip(X)
        # X = self.calculate_performance(X, [ #"naive_1", "naive_2", "naive_3",
        #                                   "slopeline_tip"]
        # )
      except Exception as error:
        raise Exception(
          f"(algorithm_v2) Encountered error on pre-game transformer: '{error}'"
        )
    else:
      try:
        print("Fitting post-game analysis dataframe (algorithm_v2) ...")
        X = self.remove_square_brackets(X)
        X = self.calculate_results(X)
        X = self.make_double_chance(X)
        X = self.make_ppg_advantages(X)
        X = self.make_slopelines(X)
        # X = self.make_naive(X)
        X = self.make_slopeline_tip(X)
        X = self.calculate_performance(X, [ #"naive_1", "naive_2", "naive_3",
                                          "slopeline_tip"]
        )
      except Exception as error:
        raise Exception(
          f"(algorithm_v2) Encountered error on post-game transformer: '{error}'"
        )
    return X

  def transform(self, X):
    assert isinstance(X, pd.DataFrame)

    if self.algorithm == "v1":
      return self.algorithm_v1(X)
    elif self.algorithm == "v2":
      return self.algorithm_v2(X)
    else:
      raise Exception("Transformer algorithm was not specified.")


class HighlightAnalysisTransformer(BaseEstimator, TransformerMixin):
  """Label fixtures' attractiveness; 'High', 'Medium', 'Low'."""
  def __init__(self):
    self.highlight_high = 0.69  # 69% and above
    self.highlight_low = 0.35   # 35% and below

  def highlight_1x(self, X):
    X["position_points"] = X.apply(
      lambda row: 1
      if (row["HTS_teamPosition"] <= row["ATS_teamPosition"] - 2.5) else (
        0.5 if (row["HTS_teamPosition"] <= row["ATS_teamPosition"] - 1.5)
        else 0.1
      ), axis=1
    )
    X["goalsdiff_points"] = X.apply(
      lambda row: 1
      if (
        (row["HTS_teamGoalsDifference"] > 0) and
        (row["HTS_teamGoalsDifference"] > row["ATS_teamGoalsDifference"] + 10)
      ) else(
        0.5 if (
          (row["HTS_teamGoalsDifference"] > 0) and
          (row["HTS_teamGoalsDifference"] > row["ATS_teamGoalsDifference"] + 5)
        ) else 0.1
      ), axis=1
    )
    X["ppgtotal_points"] = X.apply(
      lambda row: 1
      if (
        (row["HTS_advantagePpg"] > 0) and
        (row["HTS_advantagePpg"] >= 1.5)
      ) else(
        0.5 if (
          (row["HTS_advantagePpg"] > 0) and
          (row["HTS_advantagePpg"] >= 0.5)
        ) else 0.1
      ), axis=1
    )
    X["ppglast8_points"] = X.apply(
      lambda row: 1
      if (
        (row["HTS_advantagePpgLast8"] > 0) and
        (row["HTS_advantagePpgLast8"] >= 1.5)
      ) else (
        0.5 if (
          (row["HTS_advantagePpgLast8"] > 0) and
          (row["HTS_advantagePpgLast8"] >= 0.5)
        ) else 0.1
      ), axis=1
    )
    X["ppghome_points"] = X.apply(
      lambda row: 1
      if (
        (row["HTS_advantagePpgHome"] > 0) and
        (row["HTS_advantagePpgHome"] >= 1.5)
      ) else (
        0.5 if (
          (row["HTS_advantagePpgHome"] > 0) and
          (row["HTS_advantagePpgHome"] >= 0.5)
        ) else 0.1
      ), axis=1
    )
    X["ppgtrend_points"] = X.apply(
      lambda row: 1
      if ((row["HTS_teamPPGlast8"] - row["HTS_teamPointsPerGame"]) > 0) else 0.1,
      axis=1
    )
    X["pred_1x_points"] = X.apply(
      lambda row: 1
      if (row["Predictions_1x"] > row["Predictions_x2"] + 0.6) else (
        0.5 if (row["Predictions_1x"] > row["Predictions_x2"] + 0.3)
        else 0.1
      ), axis=1
    )
    X["pred_x2_points"] = X.apply(
      lambda row: 1
      if (row["Predictions_x2"] < 0.1) else (
        0.5 if (row["Predictions_x2"] < 0.3)
        else 0.1
      ), axis=1
    )

    X["highlight_total"] = X.apply(
      lambda row: np.mean([
        row["position_points"], row["goalsdiff_points"], row["ppgtotal_points"],
        row["ppglast8_points"], row["ppghome_points"], row["ppgtrend_points"],
        row["pred_1x_points"], row["pred_x2_points"]
      ]), axis=1
    )

    highlight_status = np.where(
      X["highlight_total"] >= self.highlight_high, "High",
      np.where(
        np.logical_and(
          X["highlight_total"] > self.highlight_low,
          X["highlight_total"] < self.highlight_high,
        ), "Medium",
        np.where(
          X["highlight_total"] <= self.highlight_low,
          "Low", False
        )
      )
    )
    X.drop([
      "highlight_total", "position_points", "goalsdiff_points", "ppgtotal_points",
      "ppglast8_points", "ppghome_points", "ppgtrend_points", "pred_1x_points",
      "pred_x2_points"
    ], inplace=True, axis=1)
    return highlight_status

  def highlight_x2(self, X):
    X["position_points"] = X.apply(
      lambda row: 1
      if (row["ATS_teamPosition"] <= row["HTS_teamPosition"] - 2.5) else (
        0.5 if (row["ATS_teamPosition"] <= row["HTS_teamPosition"] - 1.5)
        else 0.1
      ), axis=1
    )
    X["goalsdiff_points"] = X.apply(
      lambda row: 1
      if (
        (row["ATS_teamGoalsDifference"] > 0) and
        (row["ATS_teamGoalsDifference"] > row["HTS_teamGoalsDifference"] + 10)
      ) else(
        0.5 if (
          (row["ATS_teamGoalsDifference"] > 0) and
          (row["ATS_teamGoalsDifference"] > row["HTS_teamGoalsDifference"] + 5)
        ) else 0.1
      ), axis=1
    )
    X["ppgtotal_points"] = X.apply(
      lambda row: 1
      if (
        (row["ATS_advantagePpg"] > 0) and
        (row["ATS_advantagePpg"] >= 1.5)
      ) else(
        0.5 if (
          (row["ATS_advantagePpg"] > 0) and
          (row["ATS_advantagePpg"] >= 0.5)
        ) else 0.1
      ), axis=1
    )
    X["ppglast8_points"] = X.apply(
      lambda row: 1
      if (
        (row["ATS_advantagePpgLast8"] > 0) and
        (row["ATS_advantagePpgLast8"] >= 1.5)
      ) else (
        0.5 if (
          (row["ATS_advantagePpgLast8"] > 0) and
          (row["ATS_advantagePpgLast8"] >= 0.5)
        ) else 0.1
      ), axis=1
    )
    X["ppghome_points"] = X.apply(
      lambda row: 1
      if (
        (row["ATS_advantagePpgAway"] > 0) and
        (row["ATS_advantagePpgAway"] >= 1.5)
      ) else (
        0.5 if (
          (row["ATS_advantagePpgAway"] > 0) and
          (row["ATS_advantagePpgAway"] >= 0.5)
        ) else 0.1
      ), axis=1
    )
    X["ppgtrend_points"] = X.apply(
      lambda row: 1
      if ((row["ATS_teamPPGlast8"] - row["ATS_teamPointsPerGame"]) > 0) else 0.1,
      axis=1
    )
    X["pred_x2_points"] = X.apply(
      lambda row: 1
      if (row["Predictions_x2"] > row["Predictions_1x"] + 0.6) else (
        0.5 if (row["Predictions_x2"] > row["Predictions_1x"] + 0.3)
        else 0.1
      ), axis=1
    )
    X["pred_1x_points"] = X.apply(
      lambda row: 1
      if (row["Predictions_1x"] < 0.1) else (
        0.5 if (row["Predictions_1x"] < 0.3)
        else 0.1
      ), axis=1
    )

    X["highlight_total"] = X.apply(
      lambda row: np.mean([
        row["position_points"], row["goalsdiff_points"], row["ppgtotal_points"],
        row["ppglast8_points"], row["ppghome_points"], row["ppgtrend_points"],
        row["pred_x2_points"], row["pred_1x_points"]
      ]), axis=1
    )

    highlight_status = np.where(
      X["highlight_total"] >= self.highlight_high, "High",
      np.where(
        np.logical_and(
          X["highlight_total"] > self.highlight_low,
          X["highlight_total"] < self.highlight_high,
        ), "Medium",
        np.where(
          X["highlight_total"] <= self.highlight_low,
          "Low", False
        )
      )
    )
    X.drop([
      "highlight_total", "position_points", "goalsdiff_points", "ppgtotal_points",
      "ppglast8_points", "ppghome_points", "ppgtrend_points", "pred_x2_points",
      "pred_1x_points"
    ], inplace=True, axis=1)
    return highlight_status

  def highlight_12(self, X):
    X["pred_12_higher_points"] = X.apply(
      lambda row: 1
      if (
        (row["Predictions_12"] > 0.9) and
        (row["Predictions_1x"] < 0.8) and
        (row["Predictions_x2"] < 0.8)
      ) else 0.5, axis=1
    )
    X["pred_other_points"] = X.apply(
      lambda row: 1
      if (
        (row["Predictions_1x"] < 0.2) or
        (row["Predictions_x2"] < 0.2)
      ) else 0.5, axis=1
    )
    X["goalsdiff_points"] = X.apply(
      lambda row: 1
      if (
        abs(row["HTS_teamGoalsDifference"] - row["ATS_teamGoalsDifference"]) > 14.5
      ) else (
        0.5 if (
          abs(row["HTS_teamGoalsDifference"] - row["ATS_teamGoalsDifference"]) > 9.5
        ) else 0.1
      ), axis=1
    )
    X["ppgtotal_points"] = X.apply(
      lambda row: 1
      if (abs(row["HTS_advantagePpg"]) >= 1.5) else (
        0.5 if (abs(row["HTS_advantagePpg"]) >= 1)
        else 0.1
      ), axis=1
    )
    X["ppglast8_points"] = X.apply(
      lambda row: 1
      if (abs(row["HTS_advantagePpgLast8"]) >= 1.5) else (
        0.5 if (abs(row["HTS_advantagePpgLast8"]) >= 1)
        else 0.1
      ), axis=1
    )
    X["ppghomeaway_points"] = X.apply(
      lambda row: 1
      if (abs(row["HTS_advantagePpgHome"]) >= 1.5) else (
        0.5 if (abs(row["HTS_advantagePpgHome"]) >= 1)
        else 0.1
      ), axis=1
    )
    X["model_two_x_points"] = X.apply(
      lambda row: 1 if (row["gameDraw"] <= 0.2) else 0.5, axis=1
    )

    X["highlight_total"] = X.apply(
      lambda row: np.mean([
        row["pred_12_higher_points"], row["pred_other_points"],
        row["goalsdiff_points"], row["ppgtotal_points"], row["ppglast8_points"],
        row["ppghomeaway_points"], row["model_two_x_points"]
      ]), axis=1
    )

    highlight_status = np.where(
      X["highlight_total"] >= self.highlight_high, "High",
      np.where(
        np.logical_and(
          X["highlight_total"] > self.highlight_low,
          X["highlight_total"] < self.highlight_high,
        ), "Medium",
        np.where(
          X["highlight_total"] <= self.highlight_low,
          "Low", False
        )
      )
    )
    X.drop([
      "highlight_total", "pred_12_higher_points", "pred_other_points",
      "goalsdiff_points", "ppgtotal_points", "ppglast8_points",
      "ppghomeaway_points", "model_two_x_points"
    ], inplace=True, axis=1)
    return highlight_status

  def highlight(self, X):
    X["highlight"] = np.where(
      X["slopeline_tip"] == "1x",
      self.highlight_1x(X), # highlight 1x
      np.where(
        X["slopeline_tip"] == "x2",
        self.highlight_x2(X), # highlight x2
        np.where(
          X["slopeline_tip"] == "12",
          self.highlight_12(X), # highlight 12
          False
        )
      )
    )
    return X

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    assert isinstance(X, pd.DataFrame)
    try:
      X = self.highlight(X)
    except Exception as error:
      raise error
    return X
