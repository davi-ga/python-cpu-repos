import boto3
from os import environ
from src.scripts.io_s3 import s3_download, s3_upload, s3_delete
from src.pipelines.pipelines import load_pipeline_v1, load_inference_pipeline_v1,\
  load_highlight_analysis

s3_client = boto3.client("s3")
s3_bucket = environ.get("ARTIFACT_BUCKET")

def handler(event, context):
  """Transforms csv file data for either training or inference."""
  pipeline_type = event["pipeline_type"]
  pipeline_version = event["pipeline_version"]
  csv_filepath = event["csv_filepath"]
  csv_label = event["csv_label"]

  if pipeline_type.lower() not in ["train", "inference", "analysis"]:
    raise ValueError(f"Invalid pipeline type: '{pipeline_type}'")

  if pipeline_version.lower() not in ["pv1"]:
    raise ValueError(f"Invalid pipeline version: '{pipeline_version}'")

  csv_filename = csv_filepath.split("/")[-1]
  download_path = f"/tmp/{csv_filename}"
  s3_download(s3_client, s3_bucket, csv_filepath, download_path)

  if pipeline_type == "train":
    bucket_path_upload_train = f"data_{csv_label}/csv_train"
    bucket_path_upload_validation = f"data_{csv_label}/csv_validation"
    bucket_path_upload_archive = f"data_{csv_label}/csv_archived"

    if pipeline_version == "pv1":
      train_filename, validation_filename = load_pipeline_v1(pipeline_type, download_path, csv_label)

    # empty bucket folder contents, since it was archived earlier
    s3_delete(s3_client, s3_bucket, bucket_path_upload_train)
    s3_delete(s3_client, s3_bucket, bucket_path_upload_validation)
    # upload new bucket contents
    s3_upload(s3_client, s3_bucket, train_filename, bucket_path_upload_train)
    s3_upload(s3_client, s3_bucket, validation_filename, bucket_path_upload_validation)
    # archive new bucket contents
    s3_upload(s3_client, s3_bucket, train_filename, bucket_path_upload_archive)
    s3_upload(s3_client, s3_bucket, validation_filename, bucket_path_upload_archive)
    return True

  elif pipeline_type == "inference":
    bucket_path_upload_input = f"data_{csv_label}/csv_transforms/csv_input"
    bucket_path_upload_archive = f"data_{csv_label}/csv_transforms/csv_archived"

    if pipeline_version == "pv1":
      inference_csv_path = load_pipeline_v1(pipeline_type, download_path, csv_label)

    s3_delete(s3_client, s3_bucket, bucket_path_upload_input) # empty bucket folder
    s3_upload(s3_client, s3_bucket, inference_csv_path, bucket_path_upload_input) # upload new content
    s3_upload(s3_client, s3_bucket, inference_csv_path, bucket_path_upload_archive) # archive new content
    return True

  elif pipeline_type == "analysis":
    analysis_pipeline_version = environ.get("ANALYSIS_PIPELINE_VERSION")
    bucket_path_upload_analysis = "csv_rds/csv_analysis"
    bucket_path_upload_highlights = "csv_rds/csv_highlights"

    if analysis_pipeline_version == "pv1":
      analysis_filename = load_inference_pipeline_v1(download_path)
      highlights_filename = load_highlight_analysis(analysis_filename)

    s3_upload(s3_client, s3_bucket, analysis_filename, bucket_path_upload_analysis)
    s3_upload(s3_client, s3_bucket, highlights_filename, bucket_path_upload_highlights)

    bucket_filepath_analysis = f"{bucket_path_upload_analysis}/{analysis_filename.split('/')[-1]}"
    bucket_filepath_highlights = f"{bucket_path_upload_highlights}/{highlights_filename.split('/')[-1]}"
    return bucket_filepath_highlights
