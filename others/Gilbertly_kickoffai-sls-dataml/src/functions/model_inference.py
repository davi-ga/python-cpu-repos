import datetime
import boto3
from time import gmtime, strftime
from os import environ
from src.scripts.io_sagemaker import transform_job_describe
from src.models.inference import inference_batch_transform

sm_client = boto3.client("sagemaker")
ssm_client = boto3.client("ssm")

def handler(event, context):
  model_label = event["model_label"]
  model_metric = event["model_metric"]
  model_type = event["model_type"]

  valid_model_labels = ["1x", "x2", "12", "xc"]
  valid_model_metrics = ["mae", "rmse", "merror", "mlogloss"]

  if model_label not in valid_model_labels:
    raise ValueError(f"Invalid model label: '{model_label}'")

  if model_metric not in valid_model_metrics:
    raise ValueError(f"Invalid model metric: '{model_metric}'")

  if model_type not in ["xgb"]:
    raise ValueError(f"Invalid model type: '{model_type}'")

  model_name = f"{model_type}-{model_label}-{model_metric}"
  date_today = strftime("%d-%H-%M-%S", gmtime())
  transform_job_name = f"{model_name}-{date_today}"

  transform_job_arn = inference_batch_transform(
    sm_client, ssm_client, model_name, transform_job_name, model_label, model_type
  )

  return {
    "transform_job_name": transform_job_name,
    "transform_job_arn": transform_job_arn
  }

def inference_status(event, context):
  transform_job_name = event["transform_job_name"]

  response = transform_job_describe(sm_client, transform_job_name)
  if response:
    job_status = response["TransformJobStatus"]

    if job_status != "Completed":
      return {"job_status": job_status}
    else:
      job_output = response["TransformOutput"]["S3OutputPath"]
      print(f"Completed batch transform job with output: '{job_output}'")
      return {
        "job_status": job_status,
        "job_output": job_output
      }

def inference_start(event, context):
  query_date = datetime.datetime.today().strftime("%Y-%m-%d")
  pipeline_version = environ.get("PIPELINE_VERSION")

  model_metric_1x = environ.get("MODEL_METRIC_1X")
  model_metric_x2 = environ.get("MODEL_METRIC_X2")
  model_metric_12 = environ.get("MODEL_METRIC_12")
  model_metric_xc = environ.get("MODEL_METRIC_XC")

  model_type_1x = environ.get("MODEL_TYPE_1X")
  model_type_x2 = environ.get("MODEL_TYPE_X2")
  model_type_12 = environ.get("MODEL_TYPE_12")
  model_type_xc = environ.get("MODEL_TYPE_XC")

  params = [
    pipeline_version, model_metric_1x, model_metric_x2, model_metric_12,
    model_metric_xc, model_type_1x, model_type_x2, model_type_12, model_type_xc
  ]
  if all(param is not None for param in params):
    print(f"Starting daily inference workflow for date '{query_date}' ...")

    return {
      "query_date": query_date,
      "pipeline_version": pipeline_version,
      "model_metric_1x": model_metric_1x,
      "model_metric_x2": model_metric_x2,
      "model_metric_12": model_metric_12,
      "model_metric_xc": model_metric_xc,
      "model_type_1x": model_type_1x,
      "model_type_x2": model_type_x2,
      "model_type_12": model_type_12,
      "model_type_xc": model_type_xc
    }
  else:
    raise ValueError("Ensure that all required parameters are valid, and try again.")
