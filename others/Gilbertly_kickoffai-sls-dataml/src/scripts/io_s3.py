import boto3
from boto3.s3.transfer import S3Transfer

def s3_download(s3_client, s3_bucket, bucket_path, download_path):
  """Download a file from an S3 folder path."""
  print(f"Downloading '{bucket_path}' from S3 to '{download_path}' ...")
  try:
    s3_client.download_file(
      s3_bucket,
      bucket_path,
      download_path
    )
    print(f"Downloaded file to '{download_path}' successfully!")
    return True
  except Exception as error:
    raise Exception(f"Error downloading '{bucket_path}' from S3: {error}")

def s3_upload(s3_client, s3_bucket, filename_path, upload_path):
  """Upload a file to an S3 folder path."""
  print(f"Uploading '{filename_path}' to S3 '{upload_path}' ...")
  try:
    filename = filename_path.split("/")[-1]
    transfer = S3Transfer(s3_client)

    transfer.upload_file(
      filename_path,
      s3_bucket,
      f"{upload_path}/{filename}"
    )
    print(f"Uploaded file to '{upload_path}' successfully!")
    return True
  except Exception as error:
    raise Exception(f"Error uploading '{filename_path}' to S3: {error}")

def s3_delete(s3_client, s3_bucket, delete_path):
  """Delete objects inside an S3 folder path."""
  print(f"Deleting files on S3 path '{delete_path}' ...")
  try:
    objects_delete = []
    objects_fetch = s3_client.list_objects(
      Bucket=s3_bucket,
      Prefix=f"{delete_path}/"
    )

    for obj in objects_fetch["Contents"]:
      objects_delete.append({
        "Key": obj["Key"]
      })

    response = s3_client.delete_objects(
      Bucket=s3_bucket,
      Delete={
        "Objects": objects_delete,
        "Quiet": False
      }
    )
    deleted_files = response["Deleted"]

    print(f"Successfully deleted: '{deleted_files}'")
    return True
  except KeyError:
    print(f"Could not delete object(s) in path '{delete_path}'. Skipping ...")
  except Exception as error:
    raise Exception(f"Error deleting files on path '{delete_path}': {error}")
