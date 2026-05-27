import boto3
from os import environ
from time import gmtime, strftime
from src.models.training import model_train_hpo, model_train
from src.scripts.io_sagemaker import hpo_job_describe, train_job_describe, model_create
from src.scripts.io_ssm import ssm_get_model_param

sm_client = boto3.client("sagemaker")
ssm_client = boto3.client("ssm")
region = environ.get("REGION")

def handler(event, context):
  model_label = event["model_label"]
  model_metric = event["model_metric"]
  model_type = event["model_type"]
  job_type = event["job_type"]

  valid_model_labels = ["1x", "x2", "12", "xc"]
  valid_model_metrics = ["mae", "rmse", "merror", "mlogloss"]

  if model_label not in valid_model_labels:
    raise ValueError(f"Invalid model label: '{model_label}'")

  if model_metric not in valid_model_metrics:
    raise ValueError(f"Invalid model metric: '{model_metric}'")

  if model_type not in ["xgb"]:
    raise ValueError(f"Invalid model type: '{model_type}'")

  if job_type not in ["train", "hpo"]:
    raise ValueError(f"Invalid job type: '{job_type}'")

  date_today = strftime("%d-%H-%H-%S", gmtime())
  job_name = f"{model_type}-{model_label}-{model_metric}-{date_today}"

  if job_type == "hpo":
    tuning_job_arn = model_train_hpo(
      sm_client, ssm_client, model_type, model_label, model_metric, job_name
    )
    return {
      "job_name": job_name,
      "job_type": job_type,
      "job_arn": tuning_job_arn,
      "model_type": model_type
    }

  elif job_type == "train":
    train_job_arn = model_train()
    return {
      "job_name": job_name,
      "job_type": job_type,
      "job_arn": train_job_arn,
      "model_type": model_type
    }

def job_status(event, context):
  job_name = event["job_name"]
  job_type = event["job_type"]
  model_label = event["model_label"]
  model_metric = event["model_metric"]
  model_type = event["model_type"]

  if job_type == "hpo":
    resp_describe = hpo_job_describe(sm_client, job_name)
    if resp_describe:
      hpo_status = resp_describe["HyperParameterTuningJobStatus"]
      if hpo_status != "Completed":
        return {"job_status": hpo_status}
      else:
        best_job_name = resp_describe["BestTrainingJob"]["TrainingJobName"]
        train_job = train_job_describe(sm_client, best_job_name)

        s3_model_artifact = train_job["ModelArtifacts"]["S3ModelArtifacts"]
        s3_model_artifact_path = s3_model_artifact.split("s3://")[1]
        s3_model_url = f"https://s3-{region}-amazonaws.com/{s3_model_artifact_path}"

        model_name = f"{model_type}_{model_label}"
        model_arn = publish_model(job_type, job_name, model_name, s3_model_url)
        return {
          "job_status": hpo_status,
          "model_arn": model_arn
        }

def publish_model(job_type, job_name, model_name, s3_model_url):
  def get_param(param, param_index=None):
    """Helper function to get models' parameters."""
    return ssm_get_model_param(ssm_client, model_name, param, param_index)

  exec_role_arn = get_param("iam_role_arn")
  primary_container = {
    "Image": get_param(f"{job_type}_image"),
    "ModelDataUrl": s3_model_url
  }

  model_arn = model_create(sm_client, job_name, primary_container, exec_role_arn)
  return model_arn
