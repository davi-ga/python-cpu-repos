import boto3
from os import environ
from src.scripts.io_s3 import s3_download, s3_upload
from src.pipelines.pipelines import concat_csv_stage_one, concat_csv_stage_two

s3_client = boto3.client("s3")
s3_bucket = environ.get("ARTIFACT_BUCKET")

def concat_stage_one(event, context):
  """Concatenate Sagemaker predictions with original features csv file."""
  csv_input_path = event["csv_input_path"]
  csv_label = event["csv_label"]
  pipeline_version = event["pipeline_version"]
  filename = csv_input_path.split("/")[-1].split(".csv")[0]

  csv_output_path = f"data_{csv_label}/csv_transforms/csv_output/{filename}_inference_{pipeline_version}.csv.out"
  concat_upload_path = f"data_{csv_label}/csv_transforms/csv_readable"
  features_filepath = f"/tmp/{filename}.csv"
  predictions_filepath = f"/tmp/output_{filename}.csv"

  s3_download(s3_client, s3_bucket, csv_input_path, features_filepath)
  s3_download(s3_client, s3_bucket, csv_output_path, predictions_filepath)

  if csv_label == "xc":
    concat_csv_filepath = concat_csv_stage_one(features_filepath, predictions_filepath, csv_label, multiclass=True)
  else:
    concat_csv_filepath = concat_csv_stage_one(features_filepath, predictions_filepath, csv_label)

  resp_upload = s3_upload(s3_client, s3_bucket, concat_csv_filepath, concat_upload_path)
  if resp_upload:
    bucket_path = f"{concat_upload_path}/{concat_csv_filepath.split('/')[-1]}"
    return bucket_path

def concat_stage_two(event, context):
  """Concatenate all Sagemaker predictions with original features csv file."""
  query_date = event["query_date"]
  concat_upload_path = "csv_rds/csv_readable"
  csv_filenames = {}
  csv_labels = ["1x", "12", "x2", "xc"]

  for csv_label in csv_labels:
    filename = f"concat_{csv_label}_csv_{query_date}.csv"
    bucket_filepath = f"data_{csv_label}/csv_transforms/csv_readable/{filename}"
    download_path = f"/tmp/{filename}"

    resp_download = s3_download(s3_client, s3_bucket, bucket_filepath, download_path)
    if resp_download:
      csv_filenames.update({csv_label: download_path})

  concat_csv_filepath = concat_csv_stage_two(
    csv_filenames["1x"], csv_filenames["12"], csv_filenames["x2"], csv_filenames["xc"]
  )

  resp_upload = s3_upload(s3_client, s3_bucket, concat_csv_filepath, concat_upload_path)
  if resp_upload:
    bucket_path = f"{concat_upload_path}/{concat_csv_filepath.split('/')[-1]}"
    return bucket_path
