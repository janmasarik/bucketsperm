# low-hanging
`bucketsperm` aims to be an unified bucket permission checker for all available providers. 

It *doesn't* aim to be an enumerator, there are tools which are faster and better for it (like `massdns`, `wfuzz` or `gobuster`).

Provide a list of buckets and optionally a namespace to be used with Oracle and Azure buckets. 

## Usage
```bash
$ docker run s14ve/bucketsperm --help
Usage: bucketsperm [OPTIONS]

Options:
  -i, --input TEXT       Path to file with list of domains/IPs separated by
                         newline.
  -s, --single TEXT      Check a single bucket name
  -o, --output TEXT      Output files to file in json format.
  -t, --threads INTEGER  Number of threads with which you want to run.
  -n, --namespace TEXT   Namespace used for Oracle namespace and Azure account
                         name. Defaults to bucket name.
  -v, --verbosity LVL    Either CRITICAL, ERROR, WARNING, INFO or DEBUG
  --help                 Show this message and exit.
``` 

## Supported providers
Please see `bucketsperm/modules/*` for list of available modules. 