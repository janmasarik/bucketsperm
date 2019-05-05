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

        r = requests.get(f"{bucket_url}/{self.poc_filename}")
        if "ResourceNotFound" in r.text:
            raise BucketNotFound

        permissions = Bucket(url=bucket_url)

        r = requests.get(bucket_url, params={"restype": "container", "comp": "list"})
        permissions.read = True
        if "ResourceNotFound" not in r.text:
            permissions.list = True

        return permissions

    @staticmethod
    def validate_bucket_name(bucket_name):
        # http://docs-aliyun.cn-hangzhou.oss.aliyun-inc.com/pdf/oss-sdk-intl-en-2017-05-16.pdf
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            return False

        allowed_chars = set(string.digits + string.ascii_letters + "-")

        if any(c not in allowed_chars for c in bucket_name):
            return False

        return True
