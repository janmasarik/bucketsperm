import requests
import os
import string

from bucketsperm.models import BaseWorker, Bucket, BucketNotFound


class Azure(BaseWorker):
    name = "azure"
    references = []

    def run(self):
        bucket_url = (
            f"https://{self.azure_namespace}.blob.core.windows.net/{self.bucket_name}"
        )

        permissions = Bucket(url=bucket_url)
        r = requests.get(f"{bucket_url}/{self.poc_filename}")
        if "ResourceNotFound" in r.text:
            raise BucketNotFound

        if "BlobNotFound" in r.text:
            permissions.read = True

        r = requests.get(bucket_url, params={"restype": "container", "comp": "list"})
        if "ResourceNotFound" not in r.text:
            permissions.list_ = True

        return permissions

    @staticmethod
    def validate_bucket_name(bucket_name):
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            return False

        allowed_chars = set(string.digits + string.ascii_letters + "-")

        if any(c not in allowed_chars for c in bucket_name):
            return False

        return True
