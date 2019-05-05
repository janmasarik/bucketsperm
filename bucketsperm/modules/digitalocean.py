import boto3
import requests
import os
import string
import io
import logging

from botocore.exceptions import ClientError
from botocore.client import Config
from bucketsperm.models import BaseWorker, Bucket, BucketNotFound


log = logging.getLogger()


class DigitalOcean(BaseWorker):
    name = "digitalocean"
    references = []

    def run(self):
        region = self.detect_region(self.bucket_name)
        if not region:
            raise BucketNotFound

        client = boto3.client(
            "s3",
            region_name=region,
            config=Config(s3={"addressing_style": "virtual"}),
            endpoint_url=f"https://{region}.digitaloceanspaces.com",
            aws_access_key_id=os.getenv("DO_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("DO_SECRET_ACCESS_KEY"),
        )

        permissions = Bucket(
            url=f"https://{self.bucket_name}.{region}.digitaloceanspaces.com"
        )

        try:
            client.list_objects(Bucket=self.bucket_name)
            permissions.list_ = True
        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDenied":
                log.exception("List Bucket unexpected error!")

        try:
            client.upload_fileobj(
                io.BytesIO(b"test"), self.bucket_name, self.poc_filename
            )
            permissions.write = True
        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDenied":
                log.exception("Write bucket unexpected error!")

        bucket_acl = {}
        try:
            client = boto3.client(
                "s3",
                region_name=region,
                config=Config(s3={"addressing_style": "virtual"}),
                endpoint_url=f"https://{region}.digitaloceanspaces.com",
                aws_access_key_id=os.getenv("DO_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("DO_SECRET_ACCESS_KEY"),
            )
            bucket_acl = client.get_bucket_acl(Bucket=self.bucket_name)
            permissions.read_acp = True
        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDenied":
                log.exception("Read BucketAcl unexpected error!")

        try:
            owner = bucket_acl.get("Owner") or {
                "DisplayName": os.getenv("DO_USER_ID"),
                "ID": os.getenv("DO_USER_ID"),
            }
            bucket_acl = bucket_acl.get("Grants", [])

            bucket_acl.append(
                {
                    "Grantee": {
                        "DisplayName": os.getenv("DO_USER_ID"),
                        "ID": os.getenv("DO_USER_ID"),
                        "Type": "CanonicalUser",
                    },
                    "Permission": "FULL_CONTROL",
                }
            )

            client.put_bucket_acl(
                Bucket=self.bucket_name,
                AccessControlPolicy={"Grants": bucket_acl, "Owner": owner},
            )
            permissions.write_acp = True
        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDenied":
                log.exception("Write BucketAcl unexpected error!")

        return permissions

    @staticmethod
    def detect_region(bucket_name):
        regions = ["nyc3", "ams3", "sgp1", "sfo2"]
        for do_region in regions:
            r = requests.head(
                f"https://{bucket_name}.{do_region}.digitaloceanspaces.com"
            )
            if r.status_code in {200, 403}:
                return do_region

    @staticmethod
    def validate_bucket_name(bucket_name):
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            return False

        allowed_chars = set(string.digits + string.ascii_letters + "-")

        if any(c not in allowed_chars for c in bucket_name):
            return False

        return True