import requests
import os
import string

from bucketsperm.models import BaseWorker, Bucket, BucketNotFound


class Oracle(BaseWorker):
    name = "oracle"
    references = []

    def run(self):
        regions = ["eu-frankfurt-1", "uk-london-1", "us-phoenix-1", "us-ashburn-1"]
        for region in regions:
            if region == "uk-london-1":
                bucket_url = f"https://{self.oracle_namespace}.compat.objectstorage.{region}.oraclecloud.com/{self.bucket_name}"
            else:
                bucket_url = f"https://compat.objectstorage.{region}.oraclecloud.com/n/{self.oracle_namespace}/b/{self.bucket_name}"
            r = requests.get(f"{bucket_url}/{self.poc_filename}")
            if "NoSuchKey" in r.text:
                break
        else:
            raise BucketNotFound

        permissions = Bucket(url=bucket_url, read=True)

        r = requests.get(bucket_url)
        if "ListBucketResult" in r.text:
            permissions.list_ = True

        return permissions

    @staticmethod
    def validate_bucket_name(bucket_name):
        # https://docs.cloud.oracle.com/iaas/Content/Object/Tasks/managingbuckets.htm
        if len(bucket_name) > 256:
            return False

        allowed_chars = set(string.digits + string.ascii_letters + "-_.")

        if any(c not in allowed_chars for c in bucket_name):
            return False

        return True

