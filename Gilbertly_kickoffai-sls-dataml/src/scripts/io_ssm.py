def ssm_add_param(ssm_client, ssm_param, old_param=None):
  """Add a secret to parameter store."""
  def check_updateable_params(ssm_param, old_param):
    """Helper function to check if parameter has been modified."""
    values_changed = [
      ssm_param["Value"] != old_param["Parameter"]["Value"],
      ssm_param["Type"] != old_param["Parameter"]["Type"],
    ]
    if True in values_changed:
      return True

  param_name = ssm_param["Name"]
  if old_param:
    param_updated = check_updateable_params(ssm_param, old_param)
    if param_updated:
      param_version = ssm_update_param(ssm_client, ssm_param)
      if param_version:
        print(f"Updated parameter: '{param_name}', Version: '{param_version}'")

  else:
    param_version = ssm_update_param(ssm_client, ssm_param)
    if param_version:
      print(f"Added parameter: '{param_name}', Version: '{param_version}'")

def ssm_update_param(ssm_client, ssm_param):
  """Update an existing secret in parameter store."""
  param_name = ssm_param["Name"]
  param_description = ssm_param["Description"]
  param_value = ssm_param["Value"]
  param_type = ssm_param["Type"]
  param_overwrite = ssm_param["Overwrite"]

  try:
    if "KeyId" in ssm_param:
      response = ssm_client.put_parameter(
        Name=param_name,
        Description=param_description,
        Value=param_value,
        Type=param_type,
        Overwrite=param_overwrite,
        KeyId=ssm_param["KeyId"]
      )
    else:
      response = ssm_client.put_parameter(
        Name=param_name,
        Description=param_description,
        Value=param_value,
        Type=param_type,
        Overwrite=param_overwrite
      )
    param_version = response["Version"]
    return param_version
  except ssm_client.exceptions.ParameterAlreadyExists:
    raise Exception(f"Parameter '{param_name}' already exists.")
  except ssm_client.exceptions.ParameterPatternMismatchException:
    raise Exception(f"Parameter '{param_name}' name is not valid.")
  except ssm_client.exceptions.InvalidKeyId:
    raise Exception(f"Parameter '{param_name}' has an invalid KeyId.")
  except ssm_client.exceptions.InvalidAllowedPatternException:
    raise Exception(f"Parameter '{param_name}' does not meet regex requirement.")
  except ssm_client.exceptions.ParameterMaxVersionLimitExceeded:
    raise Exception(f"Parameter '{param_name}' has reached max allowed versions.")
  except ssm_client.exceptions.TooManyUpdates:
    raise Exception(f"Parameter '{param_name}' has too many concurrent updates.")
  except ssm_client.exceptions.UnsupportedParameterType:
    raise Exception(f"Parameter '{param_name}' has unsupported type '{param_type}'.")
  except Exception as error:
    raise Exception(f"Error modifying parameter '{param_name}': {error}")

def ssm_delete_param(ssm_client, ssm_param):
  """Delete an existing secret in parameter store."""
  param_name = ssm_param["Name"]

  try:
    ssm_client.delete_parameter(Name=param_name)
    print(f"Deleted parameter: '{param_name}'")
    return True
  except ssm_client.exceptions.ParameterNotFound:
    print(f"Parameter not found: '{param_name}'.")
    return False

def ssm_get_param(ssm_client, ssm_param):
  """Return an existing secret in parameter store."""
  param_name = ssm_param["Name"]

  try:
    response = ssm_client.get_parameter(Name=param_name)
    return response
  except ssm_client.exceptions.ParameterNotFound:
    return False
  except ssm_client.exceptions.InvalidKeyId:
    raise Exception(f"Parameter '{param_name}' has an invalid KeyId.")

def ssm_get_param_history(ssm_client, ssm_param):
  try:
    response = ssm_client.get_parameter_history(Name=ssm_param)
    return response["Parameters"][0]
  except ssm_client.exceptions.ParameterNotFound:
    print(f"Parameter not found: '{ssm_param}'")
    return False
  except ssm_client.exceptions.InvalidKeyId:
    raise Exception(f"Parameter has an invalid KeyId: '{ssm_param}'")

def ssm_get_params_by_path(ssm_client, param_path, next_token=''):
  """Return all available parameters by path."""
  try:
    if next_token == "":
      response = ssm_client.get_parameters_by_path(
        Path=param_path,
        Recursive=True,
        MaxResults=10
      )
    else:
      response = ssm_client.get_parameters_by_path(
        Path=param_path,
        Recursive=True,
        MaxResults=10,
        NextToken=next_token
      )
    return response
  except Exception as error:
    raise Exception(f"Error getting parameters in path '{param_path}': {error}")

def ssm_get_model_param(ssm_client, model_name, param_name, param_index=None):
  """Return a specific model parameter from parameter store."""
  param_config = {"Name": f"/kickoffai/dataml/{model_name}/{param_name}"}
  resp_get_param = ssm_get_param(ssm_client, param_config)

  if resp_get_param:
    param_value = resp_get_param["Parameter"]["Value"]
    if isinstance(param_index, int):
      param_value = param_value.split(",")[param_index]
    return param_value.strip(" ")

def exec_cli_command(ssm_client, ssm_filepath, action, param_path=None, parameters=[], next_token=''):
  """Run ssm operations against local config file."""
  if action in ["update", "delete"]:
    try:
      with open(ssm_filepath, "r") as ssm_file:
        ssm_params = json.loads(ssm_file.read())

      for ssm_param in ssm_params:
        if action == "update":
          resp_old_param = ssm_get_param(ssm_client, ssm_param)
          if resp_old_param:
            ssm_add_param(ssm_client, ssm_param, resp_old_param)
            sys.stdout.write(".")
            sys.stdout.flush()
          else:
            ssm_add_param(ssm_client, ssm_param)
        elif action == "delete":
          ssm_delete_param(ssm_client, ssm_param)
      print("Done!")
    except FileNotFoundError:
      print(f"Ensure the file '{ssm_filepath}' exists, and try again.")
  elif action == "download":
    response = ssm_get_params_by_path(ssm_client, param_path, next_token)
    if "NextToken" in response:
      next_token = response["NextToken"]
      parameters += response["Parameters"]
      exec_cli_command(ssm_client, ssm_filepath, action, param_path, parameters, next_token)
    else:
      parameters += response["Parameters"]
      print(f"Downloading parameters on ssm path: '{param_path}' ...")
      all_parameters = []
      for param in parameters:
        sys.stdout.write(".")
        sys.stdout.flush()
        del param["ARN"]
        resp_history = ssm_get_param_history(ssm_client, param["Name"])
        if resp_history:
          old_param = resp_history
          param.update({"Overwrite": True})
          param.update({"Description": old_param["Description"]})
        all_parameters.append(param)

      with open(ssm_filepath, "w", encoding="utf-8") as json_file:
        json.dump(all_parameters, json_file, indent=2, sort_keys=True, default=str)
      print(f"\nDownloaded ({len(all_parameters)}) ssm parameters to file: '{ssm_filepath}'")

if __name__ == "__main__":
  import os, json, argparse, boto3, sys
  from os.path import join, dirname
  from dotenv import load_dotenv
  from botocore.exceptions import NoCredentialsError

  ssm_client = boto3.client("ssm")
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--action",
    help="Action to perform on ssm parameters.",
    required=True
  )
  args = parser.parse_args()
  action = args.action
  param_path = None

  try:
    if action.lower() == "download":
      param_path = input("Enter ssm parameter path to download from [eg. '/kickoffai/dataml']: ")
      ssm_filepath = join(dirname(__file__), f"../../config/ssm.download.json")

    elif action.lower() == "update":
      param_path = input("Enter ssm parameters' filename to update from [eg. ssm.<filename>.json]: ")
      ssm_filepath = join(dirname(__file__), f"../../config/ssm.{param_path}.json")

    elif action.lower() == "delete":
      param_path = input("Enter ssm parameters' filename to delete from [eg. ssm.<filename>.json]: ")
      ssm_filepath = join(dirname(__file__), f"../../config/ssm.{param_path}.json")

    exec_cli_command(ssm_client, ssm_filepath, action, param_path)
  except NoCredentialsError:
    print("AWS cli credentials not found!")
    sys.exit(0)
  except RuntimeError:
    sys.exit(0)
  except KeyboardInterrupt:
    sys.exit(0)
