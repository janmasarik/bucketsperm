# low-hanging
`low-hanging` aims to be lightweight and extensible horizontal vulnerability scanner. 

Just pass list of domains/IPs and `low-hanging` will check for easily detectable vulnerabilities with low false positive rate.

Made to be easily extensible. Adding more checks is just few lines of code with features like JS rendering in your possession thanks to `requests-html`.

Inspired by https://github.com/tomnomnom/meg, but made to be easily pluggable into your fully automated workflow.

## Usage
```bash
$ docker run s14ve/low-hanging --help
Usage: low_hanging.py [OPTIONS]

Options:
  -i, --input TEXT       Path to file with list of domains/IPs separated by
                         newline.
  -t, --threads INTEGER  Number of threads with which you want to run.
  -o, --output TEXT      Output files to file in json format.
  --help                 Show this message and exit.
``` 

