import concurrent.futures
import click
import click_log
import json
import logging

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

from bucketsperm.models import BucketNotFound
from bucketsperm.modules import AWS, DigitalOcean, Google, AliCloud, Azure, Oracle

log = logging.getLogger()
click_log.basic_config(log)


def gather(
    buckets, threads, azure_namespace, oracle_namespace, quiet, enabled_modules_list
):

    active_modules = {
        "s3": AWS,
        "digitalocean": DigitalOcean,
        "google": Google,
        "alicloud": AliCloud,
        "azure": Azure,
        "oracle": Oracle,
    }

    if not azure_namespace:  # No need to waste egress traffic
        active_modules.pop("azure")

    if not oracle_namespace:  # No need to waste egress traffic
        active_modules.pop("oracle")

    enabled_modules = [active_modules[m] for m in enabled_modules_list]

    if not enabled_modules:  # Enable everything in case providers are not specified
        enabled_modules = active_modules.values()

    results = defaultdict(list)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        for bucket_name in tqdm(buckets, desc=" buckets", disable=quiet):
            future_to_name = {
                executor.submit(
                    worker(bucket_name, azure_namespace, oracle_namespace)
                ): worker.name
                for worker in enabled_modules
            }
            for future in tqdm(
                concurrent.futures.as_completed(future_to_name),
                total=len(future_to_name),
                unit=" providers",
                disable=quiet,
            ):
                worker_name = future_to_name[future]
                try:
                    result = future.result()
                    if not result:
                        continue

                    results[worker_name].append(result)
                except BucketNotFound:
                    pass
                except Exception as e:
                    log.info("{}\nWorker {} failed!".format(e, worker_name))

    return results


def filter_buckets(buckets_list):
    pass


@click.command()
@click.option(
    "-i",
    "--input",
    "input_file",
    help="Path to file with list of domains/IPs separated by newline.",
)
@click.option("-s", "--single", "bucket_name", help="Check a single bucket name")
@click.option(
    "-o",
    "--output",
    "output_file",
    help="Output all results to a file with corresponding permissions in json format.",
)
@click.option(
    "-t", "--threads", default=50, help="Number of threads with which you want to run."
)
@click.option(
    "--only-readable-file",
    "only_readable_file",
    default=False,
    help="Output buckets which are confirmed to be readable.",
)
@click.option(
    "--only-vulnerable-file",
    "only_vulnerable_file",
    default=False,
    help="Output buckets with LIST, WRITE, READ_ACP or WRITE_ACP enabled.",
)
@click.option(
    "--enabled-providers",
    "enabled_providers",
    default="",
    help="Comma separated list of enabled providers. Example: 's3,google,amazon'. Defaults to all.",
)
@click.option(
    "--azure-namespace",
    "azure_namespace",
    help="Azure account name. Needs to be bruteforced in advance. If not specified, azure module will not run.",
)
@click.option(
    "--oracle-namespace",
    "oracle_namespace",
    help="Oracle namespace name. Needs to be _guessed_ in advance as Oracle doesn't allow easy bruteforcing (please contact me if you'll find an easy way). If not specified, oracle module will not run.",
)
@click.option("-q", "--quiet", is_flag=True, help="Disable progress bar")
@click_log.simple_verbosity_option(log)
def main(
    input_file,
    bucket_name,
    threads,
    output_file,
    only_readable_file,
    only_vulnerable_file,
    azure_namespace,
    oracle_namespace,
    enabled_providers,
    quiet,
):
    input_buckets = []
    if input_file:
        with open(input_file) as input_buckets_file:
            input_buckets = input_buckets_file.read().splitlines()
    elif bucket_name:
        input_buckets = [bucket_name]

    if enabled_providers:
        enabled_providers = enabled_providers.replace(" ", "").split(",")

    results = gather(
        input_buckets,
        threads,
        azure_namespace,
        oracle_namespace,
        quiet,
        enabled_providers,
    )

    results_list = [
        bucket for provider, buckets in results.items() for bucket in buckets
    ]

    parsed_results = [bucket.to_string() for bucket in results_list]

    click.echo("\n".join(sorted(parsed_results)))

    if output_file:
        with open(output_file, "w") as f:
            f.write("\n".join(sorted(parsed_results)) + "\n" if parsed_results else "")

    if only_readable_file:
        readable = [bucket.to_string() for bucket in results_list if bucket.read]
        with open(only_readable_file, "w") as f:
            f.write("\n".join(sorted(readable)) + "\n" if readable else "")

    if only_vulnerable_file:
        vulnerable = [
            bucket.to_string()
            for bucket in results_list
            if any((bucket.list_, bucket.write, bucket.write_acp))
        ]
        with open(only_vulnerable_file, "w") as f:
            f.write("\n".join(sorted(vulnerable)) + "\n" if vulnerable else "")


if __name__ == "__main__":
    main()
