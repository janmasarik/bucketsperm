import requests
import os
import string

from google.cloud import storage
from google.oauth2 import service_account

from bucketsperm.models import BaseWorker, Bucket, BucketNotFound


class Google(BaseWorker):
    """Inspired by https://github.com/RhinoSecurityLabs/GCPBucketBrute"""

    name = "google"
    references = []

    def run(self):

        if not self.check_existence(self.bucket_name):
            raise BucketNotFound

        client = None
        if os.getenv("GOOGLE_SERVICE_ACCOUNT_FILEPATH"):
            credentials = service_account.Credentials.from_service_account_file(
                os.getenv("GOOGLE_SERVICE_ACCOUNT_FILEPATH")
            )
            client = storage.Client(project=None, credentials=credentials)

        permissions = Bucket(
            url=f"https://www.googleapis.com/storage/v1/b/{self.bucket_name}"
        )

        if client:
            authenticated_permissions = client.bucket(
                self.bucket_name
            ).test_iam_permissions(
                permissions=[
                    "storage.buckets.delete",
                    "storage.buckets.get",
                    "storage.buckets.getIamPolicy",
                    "storage.buckets.setIamPolicy",
                    "storage.buckets.update",
                    "storage.objects.create",
                    "storage.objects.delete",
                    "storage.objects.get",
                    "storage.objects.list",
                    "storage.objects.update",
                ]
            )
            if authenticated_permissions:
                if "storage.objects.get" in authenticated_permissions:
                    permissions.read = True
                if "storage.objects.list" in authenticated_permissions:
                    permissions.list_ = True
                if (
                    "storage.objects.create" in authenticated_permissions
                    or "storage.objects.delete" in authenticated_permissions
                    or "storage.objects.update" in authenticated_permissions
                ):
                    permissions.write = True
                if "storage.buckets.setIamPolicy" in authenticated_permissions:
                    permissions.read_acp = True
                if "storage.buckets.setIamPolicy" in authenticated_permissions:
                    permissions.write_acp = True

        unauthenticated_permissions = requests.get(
            "https://www.googleapis.com/storage/v1/b/{}/iam/testPermissions?permissions=storage.buckets.delete&permissions=storage.buckets.get&permissions=storage.buckets.getIamPolicy&permissions=storage.buckets.setIamPolicy&permissions=storage.buckets.update&permissions=storage.objects.create&permissions=storage.objects.delete&permissions=storage.objects.get&permissions=storage.objects.list&permissions=storage.objects.update".format(
                self.bucket_name
            )
        ).json()

        unauthenticated_permissions = unauthenticated_permissions.get("permissions")
        if unauthenticated_permissions:
            if "storage.objects.get" in unauthenticated_permissions:
                permissions.read = True
            if "storage.objects.list" in unauthenticated_permissions:
                permissions.list_ = True
            if (
                "storage.objects.create" in unauthenticated_permissions
                or "storage.objects.delete" in unauthenticated_permissions
                or "storage.objects.update" in unauthenticated_permissions
            ):
                permissions.write = True
            if "storage.buckets.setIamPolicy" in unauthenticated_permissions:
                permissions.read_acp = True
            if "storage.buckets.setIamPolicy" in unauthenticated_permissions:
                permissions.write_acp = True

        return permissions

    def check_existence(self, bucket_name):
        # Check if bucket exists before trying to TestIamPermissions on it
        response = requests.head(
            "https://www.googleapis.com/storage/v1/b/{}".format(bucket_name)
        )
        if response.status_code not in [400, 404]:
            return True
        return False

    @staticmethod
    def validate_bucket_name(bucket_name):
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            return False

        allowed_chars = set(string.digits + string.ascii_letters + "-_.")

        if any(c not in allowed_chars for c in bucket_name):
            return False

        if any(
            c not in set(string.ascii_lowercase + string.digits)
            for c in [bucket_name[0], bucket_name[-1]]
        ):
            return False

        return True
