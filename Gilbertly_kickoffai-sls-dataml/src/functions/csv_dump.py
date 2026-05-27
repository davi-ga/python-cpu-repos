import boto3
import csv
import pandas as pd
from os import environ
from src.scripts.io_s3 import s3_upload, s3_download
from src.pipelines import db_column_names

s3_client = boto3.client("s3")
rds_client = boto3.client("rds-data")

s3_bucket = environ.get("ARTIFACT_BUCKET")
db_name = environ.get("DB_NAME")
db_table = environ.get("DB_TABLE")
db_cluster_arn = environ.get("DB_CLUSTER_ARN")
db_secret_arn = environ.get("DB_SECRET_ARN")

def handler(event, context):
  query_type = event["query_type"]
  if query_type not in ["daily", "weekly"]:
    raise ValueError(f"Query type '{query_type}' is not valid!")

  if query_type == "daily":
    query_date = event["query_date"]
    sql_statement = f"select * from {db_table} where gamePlayDate='{query_date}'"
    csv_filename = f"/tmp/csv_{query_date}.csv"

    response = send_sql(db_name, db_secret_arn, db_cluster_arn, sql_statement)
    if response:
      save_to_csv(response, csv_filename)

    bucket_path = "csv_rds/csv_queries"
    resp_upload = s3_upload(s3_client, s3_bucket, csv_filename, bucket_path)
    if resp_upload:
      bucket_filename = csv_filename.split("/")[-1]
      bucket_filename_path = f"{bucket_path}/{bucket_filename}"
      return bucket_filename_path

  elif query_type == "weekly":
    query_dates = event["query_dates"]
    csv_files = []
    for date in query_dates:
      sql_statement = f"select * from {db_table} where gamePlayDate='{date}'"
      csv_filename = f"/tmp/csv_{date}.csv"

      response = send_sql(db_name, db_secret_arn, db_cluster_arn, sql_statement)
      if response:
        save_to_csv(response, csv_filename)
        csv_files.append(csv_filename)

    csv_file_df = pd.concat([pd.read_csv(csv_file) for csv_file in csv_files])
    start_date, end_date = query_dates[-1], query_dates[0]
    concat_csv_filename = f"/tmp/csv_{start_date}_{end_date}.csv"
    csv_file_df.to_csv(concat_csv_filename, index=False, encoding="utf-8")

    bucket_path = "csv_rds/csv_queries"
    resp_upload = s3_upload(s3_client, s3_bucket, concat_csv_filename, bucket_path)
    if resp_upload:
      return append_to_master(concat_csv_filename)

def append_to_master(csv_filename):
  master_filename = "csv_master.csv"
  master_bucket_path = f"csv_rds/csv_dump"
  master_download_path = f"/tmp/{master_filename}"

  s3_download(s3_client, s3_bucket, f"{master_bucket_path}/{master_filename}", master_download_path)
  updated_master_df = pd.concat([pd.read_csv(csv_file) for csv_file in [master_download_path, csv_filename]])
  updated_master_df.to_csv(master_download_path, index=False, encoding="utf-8")
  s3_upload(s3_client, s3_bucket, master_download_path, master_bucket_path)
  print(f"Appended '{csv_filename}' into master csv file!")
  return f"{master_bucket_path}/{master_filename}"

def send_sql(db_name, db_secret_arn, db_cluster_arn, sql_statement, params=[]):
  try:
    response = rds_client.execute_statement(
      database=db_name,
      secretArn=db_secret_arn,
      resourceArn=db_cluster_arn,
      sql=sql_statement,
      parameters=params
    )
    return response
  except rds_client.exceptions.StatementTimeoutException:
    raise Exception("Sql statement timed out. Try again after a while.")
  except rds_client.exceptions.ForbiddenException:
    raise Exception("Insufficient permissions to run sql statement.")
  except Exception as error:
    raise Exception(f"Error while executing sql statement: {error}")

def save_to_csv(response, csv_filename):
  def formatField(field):
    return list(field.values())[0]
  def formatRecord(record):
    return [formatField(field) for field in record]
  def formatRecords(records):
    return [formatRecord(record) for record in records]

  with open(csv_filename, "w") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(db_column_names)
    writer.writerows(formatRecords(response['records']))
  print(f"Successfully saved csv records to '{csv_filename}'!")
