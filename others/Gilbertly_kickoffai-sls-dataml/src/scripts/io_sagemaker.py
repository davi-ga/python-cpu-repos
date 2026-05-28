def train_job_create(sm_client, training_job_name, training_job_config):
  """API call to create a training job."""
  print(f"Creating training job '{training_job_name}' ...")
  try:
    response = sm_client.create_training_job(
      TrainingJobName=training_job_name
    )
    return response
  except sm_client.exceptions.ResourceInUse:
    raise Exception(f"Resource is already in use.")
  except sm_client.exceptions.ResourceLimitExceeded:
    raise Exception(f"Resource limit reached. Retry after a while.")

def train_job_describe(sm_client, training_job_name):
  """API call to describe a training job."""
  try:
    response = sm_client.describe_training_job(
      TrainingJobName=training_job_name
    )
    return response
  except sm_client.exceptions.ResourceNotFound:
    raise Exception(f"Training job not found: '{training_job_name}'")

def hpo_job_create(sm_client, tuning_job_name, tuning_job_config, training_job_config, warm_start_config=None):
  """API call to create a hyperparameter tuning job."""
  try:
    if (warm_start_config):
      response = sm_client.create_hyper_parameter_tuning_job(
        HyperParameterTuningJobName=tuning_job_name,
        HyperParameterTuningJobConfig=tuning_job_config,
        TrainingJobDefinition=training_job_config,
        WarmStartConfig=warm_start_config
      )
      print(f"Starting hyperparameter job with warmstart configuration: '{tuning_job_name}' ...")
    else:
      response = sm_client.create_hyper_parameter_tuning_job(
        HyperParameterTuningJobName=tuning_job_name,
        HyperParameterTuningJobConfig=tuning_job_config,
        TrainingJobDefinition=training_job_config
      )
      print(f"Starting hyperparameter job with configuration: '{tuning_job_name}' ...")

    tuning_job_arn = response["HyperParameterTuningJobArn"]
    return tuning_job_arn
  except sm_client.exceptions.ResourceInUse:
    raise Exception(f"Hyperparameter job resource already in use: '{tuning_job_name}'")

def hpo_job_describe(sm_client, tuning_job_name):
  """API call to describe a hyperparameter tuning job."""
  try:
    response = sm_client.describe_hyper_parameter_tuning_job(
      HyperParameterTuningJobName=tuning_job_name
    )
    return response
  except sm_client.exceptions.ResourceNotFound:
    raise Exception(f"Hyperparameter job not found: '{tuning_job_name}'")

def hpo_job_list(sm_client, tuning_job_name):
  """API call to get available hyperparameter tuning jobs."""
  try:
    response = sm_client.list_hyper_parameter_tuning_jobs(
      NameContains=tuning_job_name,
      SortOrder="Ascending",
      SortBy="CreationTime",
      StatusEquals="Completed",
      MaxResults=10
    )
    hyperparam_jobs = response["HyperParameterTuningJobSummaries"]
    return hyperparam_jobs
  except Exception as error:
    raise Exception(f"Error getting hyperparameter jobs: {error}")

def transform_job_create(sm_client, transform_job_config):
  """API call to create a batch-transform inference job."""
  transform_job_name = transform_job_config["JobName"]
  transform_model_name = transform_job_config["ModelName"]
  transform_input = transform_job_config["Input"]
  transform_output = transform_job_config["Output"]
  transform_resources = transform_job_config["Resources"]
  print(f"Starting batch transform job '{transform_job_name}' with model '{transform_model_name}' ...")

  try:
    response = sm_client.create_transform_job(
      TransformJobName=transform_job_name,
      ModelName=transform_model_name,
      MaxConcurrentTransforms=0,
      BatchStrategy="SingleRecord",
      TransformInput=transform_input,
      TransformOutput=transform_output,
      TransformResources=transform_resources
    )

    transform_job_arn = response["TransformJobArn"]
    return transform_job_arn
  except sm_client.exceptions.ResourceInUse:
    raise Exception(f"Transform job already in use: '{transform_job_name}'")

def transform_job_describe(sm_client, transform_job_name):
  """API call to describe a batch-transform inference job."""
  try:
    response = sm_client.describe_transform_job(TransformJobName=transform_job_name)
    return response
  except sm_client.exceptions.ResourceNotFound:
    raise Exception(f"Transform job not found: '{transform_job_name}'")

def model_create(sm_client, model_name, primary_container, exec_role_arn):
  """API call to create a model inside Sagemaker."""
  print(f"Creating model '{model_name}' ...")
  try:
    response = sm_client.create_model(
      ModelName=model_name,
      PrimaryContainer=primary_container,
      ExecutionRoleArn=exec_role_arn
    )

    model_arn = response["ModelArn"]
    return model_arn
  except sm_client.exceptions.ResourceLimitExceeded:
    raise Exception(f"Model resource creation limit reached: '{model_name}'")
  except Exception as error:
    raise Exception(f"Error creating model: {error}")

def model_list(sm_client, model_name):
  """API call to get available models inside Sagemaker."""
  try:
    response = sm_client.list_models(NameContains=model_name)
    recent_models = response["Models"]
    return recent_models
  except Exception as error:
    raise Exception(f"Error listing models: {error}")

def noteboook_create():
  """API call to create a jupyter notebook environment."""
  pass
