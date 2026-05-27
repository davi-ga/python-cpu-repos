from src.scripts.io_ssm import ssm_get_model_param
from src.scripts.io_sagemaker import hpo_job_list, hpo_job_create

def xgboost_x2(sm_client, ssm_client, model_label, model_metric, tuning_job_name, param_prefix):
  """XGBoost binary classification model for the 'x2' label."""
  if param_prefix == "hpo_":
    hpo_config = get_hpo_config(sm_client, ssm_client, model_label, model_metric)
    tuning_job_config = hpo_config["tuning_job_config"]
    training_job_config = hpo_config["training_job_config"]

    warm_start_config = {}
    hyperparam_jobs = hpo_job_list(sm_client, tuning_job_name)

    if len(hyperparam_jobs) > 0:
      parent_jobs = []
      for job in hyperparam_jobs:
        parent_jobs.append({
          "HyperParameterTuningJobName": job["HyperParameterTuningJobName"]
        })

      warm_start_config.update({
        "ParentHyperParameterTuningJobs": parent_jobs,
        "WarmStartType": "IdenticalDataAndAlgorithm"
      })
    else:
      print(f"No previous hyperparameter jobs to warmstart from: '{hyperparam_jobs}'")

    tuning_job_arn = hpo_job_create(
      sm_client, tuning_job_name, tuning_job_config, training_job_config, warm_start_config
    )
    return tuning_job_arn
  elif param_prefix == "train_":
    pass

def get_hpo_config(sm_client, ssm_client, model_label, model_metric):
  """Return XGBoost hyperparameter tuning config for the 'x2' label."""
  def get_param(param, param_index=None):
    """Helper function to get models' hyperparameters."""
    return ssm_get_model_param(ssm_client, f"xgb_{model_label}", param, param_index)

  s3_bucket = get_param("s3_bucket")

  training_job_config = {
    "AlgorithmSpecification": {
      "TrainingImage": get_param("hpo_image"),
      "TrainingInputMode": "File"
    },
    "RoleArn": get_param("iam_role_arn"),
    "ResourceConfig": {
      "InstanceCount": int(get_param("hpo_instance_count")),
      "InstanceType": get_param("hpo_instance_type"),
      "VolumeSizeInGB": int(get_param("hpo_instance_volume"))
    },
    "StaticHyperParameters": {
      "objective": get_param("hpo_objective"),
      "eval_metric": get_param(f"hpo_eval_metric_{model_metric}"),
      "rate_drop": get_param("hpo_rate_drop"),
      "seed": get_param("hpo_seed"),
      "early_stopping_rounds": get_param("hpo_early_stop")
    },
    "StoppingCondition": {
      "MaxRuntimeInSeconds": int(get_param("hpo_job_timeout"))
    },
    "InputDataConfig": [
      {
        "ChannelName": "train",
        "ContentType": "csv",
        "CompressionType": "None",
        "DataSource": {
          "S3DataSource": {
            "S3DataType": "S3Prefix",
            "S3Uri": f"s3://{s3_bucket}/data_{model_label}/csv_train",
            "S3DataDistributionType": "FullyReplicated"
          }
        }
      },
      {
        "ChannelName": "validation",
        "ContentType": "csv",
        "CompressionType": "None",
        "DataSource": {
          "S3DataSource": {
            "S3DataType": "S3Prefix",
            "S3Uri": f"s3://{s3_bucket}/data_{model_label}/csv_validation",
            "S3DataDistributionType": "FullyReplicated"
          }
        }
      }
    ],
    "OutputDataConfig": {
      "S3OutputPath": f"s3://{s3_bucket}/data_{model_label}/hpo_outputs"
    }
  }

  tuning_job_config = {
    "Strategy": "Bayesian",
    "HyperParameterTuningJobObjective": {
      "MetricName": get_param(f"hpo_objective_{model_metric}", 0),
      "Type": get_param(f"hpo_objective_{model_metric}", 1)
    },
    "ParameterRanges": {
      "CategoricalParameterRanges": [],
      "ContinuousParameterRanges": [
        {
          "Name": "eta",
          "MinValue": get_param("hpo_eta_range", 0),
          "MaxValue": get_param("hpo_eta_range", 1)
        },
        {
          "Name": "subsample",
          "MinValue": get_param("hpo_subsample_range", 0),
          "MaxValue": get_param("hpo_subsample_range", 1)
        },
        {
          "Name": "gamma",
          "MinValue": get_param("hpo_gamma_range", 0),
          "MaxValue": get_param("hpo_gamma_range", 1)
        },
        {
          "Name": "colsample_bytree",
          "MinValue": get_param("hpo_colsample_bytree_range", 0),
          "MaxValue": get_param("hpo_colsample_bytree_range", 1)
        }
      ],
      "IntegerParameterRanges": [
        {
          "Name": "num_round",
          "MinValue": get_param("hpo_num_round_range", 0),
          "MaxValue": get_param("hpo_num_round_range", 1)
        },
        {
          "Name": "max_depth",
          "MinValue": get_param("hpo_max_depth_range", 0),
          "MaxValue": get_param("hpo_max_depth_range", 1)
        },
        {
          "Name": "max_delta_step",
          "MinValue": get_param("hpo_max_delta_step_range", 0),
          "MaxValue": get_param("hpo_max_delta_step_range", 1)
        },
        {
          "Name": "min_child_weight",
          "MinValue": get_param("hpo_min_child_weight_range", 0),
          "MaxValue": get_param("hpo_min_child_weight_range", 1)
        }
      ]
    },
    "ResourceLimits": {
      "MaxNumberOfTrainingJobs": int(get_param("hpo_max_train_jobs")),
      "MaxParallelTrainingJobs": int(get_param("hpo_max_parallel_jobs"))
    }
  }

  return {
    "training_job_config": training_job_config,
    "tuning_job_config": tuning_job_config
  }

def start_training():
  """Start XGBoost training for the 'x2' label."""
  pass
