import json
import string

from dataclasses import dataclass
from urllib.parse import urljoin


class BucketNotFound(Exception):
    pass


class BaseWorker:
    name = "default"

    def __init__(self, bucket_name, azure_namespace=None, oracle_namespace=None):
        self.bucket_name = bucket_name
        self.azure_namespace = azure_namespace
        self.oracle_namespace = oracle_namespace
        self.poc_filename = "poc42"
        self.poc_text = b"Hello. This could have possibly been any malicious payload served from your infrastructure.\nPlease fix permissions of your bucket as soon as possible, \nas allowing WRITE to your bucket to anyone can potentially have devastating consequences."

    def __call__(self, *args, **kwargs):
        if self.validate_bucket_name(self.bucket_name):
            return self.run(*args, **kwargs)

    def run(self):
        raise NotImplementedError


@dataclass
class Bucket:
    url: str
    read: bool = False
    list_: bool = False
    write: bool = False
    read_acp: bool = False
    write_acp: bool = False

    def to_string(self):
        permissions = [
            name
            for name, acl in zip(
                ["READ", "LIST", "WRITE", "READ_ACP", "WRITE_ACP"],
                [self.read, self.list_, self.write, self.read_acp, self.write_acp],
            )
            if acl is True
        ]

        return ",".join([self.url] + permissions)

