from src.scripts.io_sagemaker import hpo_job_create, hpo_job_list
from src.scripts.io_ssm import ssm_get_param

def model_train():
  """Get model training config and start training job."""
  pass

def model_train_hpo(sm_client, ssm_client, model_type, model_label, model_metric, tuning_job_name):
  """Return the hyperparameter training job's arn, if successfully started."""
  param_prefix = "hpo_"
  if model_type == "xgb":
    if model_label == "1x":
      from src.models.xgboost.xgb_1x import xgboost_1x
      return xgboost_1x(
        sm_client, ssm_client, model_label, model_metric, tuning_job_name, param_prefix
      )

    elif model_label == "x2":
      from src.models.xgboost.xgb_x2 import xgboost_x2
      return xgboost_x2(
        sm_client, ssm_client, model_label, model_metric, tuning_job_name, param_prefix
      )

    elif model_label == "12":
      from src.models.xgboost.xgb_12 import xgboost_12
      return xgboost_12(
        sm_client, ssm_client, model_label, model_metric, tuning_job_name, param_prefix
      )

    elif model_label == "xc":
      from src.models.xgboost.xgb_xc import xgboost_xc
      return xgboost_xc(
        sm_client, ssm_client, model_label, model_metric, tuning_job_name, param_prefix
      )

  else:
    raise ValueError(f"Model type '{model_type}' is not valid.")
