import requests
import os
import re
import string

from bucketsperm.models import BaseWorker, Bucket, BucketNotFound


class AliCloud(BaseWorker):
    name = "AliCloud"
    references = []

    def run(self):
        bucket_url = f"https://{self.bucket_name}.oss-eu-west-1.aliyuncs.com"
        r = requests.get(bucket_url)
        if "NoSuchBucket" in r.text:
            raise BucketNotFound

        if "AccessDenied" in r.text:
            if (
                "The bucket you are attempting to access must be addressed using the specified endpoint."
                in r.text
            ):
                result = re.search("<Endpoint>(.*)</Endpoint>", r.text)
                bucket_url = f"https://{self.bucket_name}.{result.group(1)}"
                r = requests.get(bucket_url)

            if "Anonymous user has no right to access this bucket." in r.text:
                return Bucket(url=bucket_url)

            if "The bucket you visit is not belong to you" in r.text:
                r = requests.put(f"{bucket_url}/{self.poc_filename}", data=b"test")
                if r.status_code == 200:
                    return Bucket(url=bucket_url, read=True, write=True)

                return Bucket(url=bucket_url, read=True)
    
    @staticmethod
    def validate_bucket_name(bucket_name):
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            return False

        allowed_chars = set(string.digits + string.ascii_lowercase + "-")

        if any(c not in allowed_chars for c in bucket_name):
            return False

        if bucket_name[0] not in set(string.ascii_letters + string.digits):
            return False

        return True
