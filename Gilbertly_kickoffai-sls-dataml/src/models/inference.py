from src.scripts.io_sagemaker import transform_job_create, model_list
from src.scripts.io_ssm import ssm_get_param, ssm_get_model_param

def inference_batch_transform(sm_client, ssm_client, model_name, transform_job_name, model_label, model_type):
  """Get all config together and start a batch transform job."""
  def get_param(param, param_index=None):
    """Helper function to get models' hyperparameters."""
    return ssm_get_model_param(ssm_client, f"{model_type}_{model_label}", param, param_index)

  instance_type = get_param("instance_type_transform")
  instance_count = get_param("instance_count_transform")
  s3_bucket = get_param("s3_bucket")

  recent_models = model_list(sm_client, model_name)
  if len(recent_models) < 1:
    raise Exception(f"Could not find recent model matching: '{model_name}'")

  recent_model_name = recent_models[0]["ModelName"]
  s3_input_path = f"s3://{s3_bucket}/data_{model_label}/csv_transforms/csv_input"
  s3_output_path = f"s3://{s3_bucket}/data_{model_label}/csv_transforms/csv_output"

  transform_input = {
    "ContentType": "text/csv",
    "SplitType": "Line",
    "DataSource": {
      "S3DataSource": {
        "S3DataType": "S3Prefix",
        "S3Uri": s3_input_path
      }
    }
  }
  transform_output = {
    "S3OutputPath": s3_output_path,
    "AssembleWith": "Line"
  }
  transform_resources = {
    "InstanceType": instance_type,
    "InstanceCount": int(instance_count)
  }
  transform_job_config = {
    "JobName": transform_job_name,
    "ModelName": recent_model_name,
    "Input": transform_input,
    "Output": transform_output,
    "Resources": transform_resources
  }

  transform_job_arn = transform_job_create(sm_client, transform_job_config)
  return transform_job_arn
