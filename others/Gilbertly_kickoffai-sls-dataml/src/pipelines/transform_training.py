import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.class_weight import compute_sample_weight


class BucketizeTransformer(BaseEstimator, TransformerMixin):
  def __init__(self, columns, bins, single_col=False):
    self.columns = columns
    self.bins = bins
    self.labels = []
    self.single_col = single_col
    self.postfix = "_bin"
    self.prefix = ["HTS_", "ATS_"]

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    assert isinstance(X, pd.DataFrame)
    assert isinstance(self.columns, list)
    assert isinstance(self.bins, list)

    for bucket in self.bins[1:]:
      self.labels.append(str(bucket) + self.postfix)

    for column in self.columns:
      if self.single_col:
        X[column] = pd.cut(
          X[column],
          bins=self.bins,
          labels=self.labels
        )
      else:
        for prefix in self.prefix:
          col = prefix + column
          X[col] = pd.cut(
            X[col],
            bins=self.bins,
            labels=self.labels
          )

    return X


class GamesPlayedTransformer(BaseEstimator, TransformerMixin):
  def __init__(self):
    self.prefix = ["HTS_", "ATS_"]
    self.base_column = "teamGamesPlayed"
    self.columns = [
      "teamGamesWon", "teamGamesDraw", "teamGamesLost"
    ]

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    assert isinstance(X, pd.DataFrame)

    for column in self.columns:
      for prefix in self.prefix:
        col = prefix + column
        base_col = prefix + self.base_column
        X[col] = (X[col] / X[base_col]) * 100

    for base_col_prefix in self.prefix:
      base_col = base_col_prefix + self.base_column
      X = X.drop(base_col, axis=1)

    return X


class CleanSheetsTransformer(BaseEstimator, TransformerMixin):
  def __init__(self):
    self.prefix = ["HTS_", "ATS_"]
    self.column = "teamCleanSheetPercent"

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    assert isinstance(X, pd.DataFrame)

    for prefix in self.prefix:
      col = prefix + self.column
      X[col] = X[col].apply(
        lambda row: int(row.split("%")[0])
      )

    return X


class TeamPositionTransformer(BaseEstimator, TransformerMixin):
  def __init__(self):
    self.prefix = ["HTS_", "ATS_"]
    self.column = "teamPosition"

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    assert isinstance(X, pd.DataFrame)

    X["gamePosAdvantage"] = np.where(
      X["HTS_teamPosition"] < X["ATS_teamPosition"], # condition
      X["ATS_teamPosition"] - X["HTS_teamPosition"], # true
      X["ATS_teamPosition"] - X["HTS_teamPosition"] # false
    )

    # X["ATS_posAdvantage"] = np.where(
    #   X["ATS_teamPosition"] < X["HTS_teamPosition"], # condition
    #   X["HTS_teamPosition"] - X["ATS_teamPosition"], # true
    #   X["HTS_teamPosition"] - X["ATS_teamPosition"] # false
    # )

    for prefix in self.prefix:
      col = prefix + self.column
      X = X.drop(col, axis=1)

    return X


class FtScoresTransformer(BaseEstimator, TransformerMixin):
  def __init__(self, label=None):
    self.column = "gameFtScore"
    self.column_class_weights = "gameFtScoreWeights"
    self.label = label
    self.valid_labels = ["1x", "x2", "12", "xc", "u25", "u35", "gg"]

  def fit(self, X, y=None):
    return self

  def transform(self, X):
    assert isinstance(X, pd.DataFrame)

    if self.label is None:
      print(f"Transforming 'ftscores' ...")
      X = X.drop(self.column, axis=1)
      return X

    else:
      assert isinstance(self.label, str)
      if self.label not in self.valid_labels:
        raise ValueError(f"Invalid csv_label: '{self.label }'")

    print(f"Transforming 'ftscores', label: '{self.label}' ...")

    if self.label == "1x":
      X[self.column] = X[self.column].apply(
        lambda row:
        1 if int(row.split("-")[0]) >=
        int(row.split("-")[1]) else 0
      )
      return X

    elif self.label == "x2":
      X[self.column] = X[self.column].apply(
        lambda row:
        1 if int(row.split("-")[0]) <=
        int(row.split("-")[1]) else 0
      )
      return X

    elif self.label == "12":
      X[self.column] = X[self.column].apply(
        lambda row:
        1 if int(row.split("-")[0]) !=
        int(row.split("-")[1]) else 0
      )
      return X

    elif self.label == "u25":
      X[self.column] = X[self.column].apply(
        lambda row:
        1 if (int(row.split("-")[0]) +
        int(row.split("-")[1])) > 2 else 0
      )
      return X

    elif self.label == "u35":
      X[self.column] = X[self.column].apply(
        lambda row:
        1 if (int(row.split("-")[0]) +
        int(row.split("-")[1])) > 3 else 0
      )
      return X

    elif self.label == "gg":
      X[self.column] = X[self.column].apply(
        lambda row:
        1 if (int(row.split("-")[0]) > 0 and
        int(row.split("-")[1]) > 0) else 0
      )
      return X

    elif self.label == "xc":
      X[self.column] = X[self.column].apply(
        lambda row: self._transform_xc(row)
      )

      X[self.column_class_weights] = compute_sample_weight(
        class_weight="balanced",
        y=X[self.column].values
      )

      X = X.loc[:, [self.column] + [self.column_class_weights] + X.columns[1:-1].tolist()]

      return X

  def _transform_xc(self, row):
    try:
      first_split = int(row.split("-")[0])
      second_split = int(row.split("-")[1])

      if first_split > second_split:
        return 0 # label 1
      elif first_split < second_split:
        return 1 # label 2
      elif first_split == second_split:
        return 2 # label x
      else:
        raise ValueError(f"Unknown row value: '{row}'")
    except Exception as error:
      raise Exception(f"Encountered error: '{error}'")
