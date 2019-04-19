import click


def generate_permutations(keyword, wordlist):
    res = []
    permutation_templates = [
        "{keyword}-{permutation}",
        "{permutation}-{keyword}",
        "{keyword}_{permutation}",
        "{permutation}_{keyword}",
        "{keyword}{permutation}",
        "{permutation}{keyword}",
        "{keyword}.{permutation}",
        "{permutation}.{keyword}",
        "{keyword}",
        "{permutation}",
    ]

    for word in wordlist:
        for permuntation in permutation_templates:
            res.append(permuntation.format(keyword=keyword, permutation=word))

    return res


@click.command()
@click.option("-d", "--domains", help="List of domains")
@click.option("-sd", "--domain", help="Single domain name")
@click.option(
    "-w", "--wordlist", help="List of possible bucket names like admin, dev, logs"
)
@click.option("-o", "--output", help="Output file name")
def main(domains, domain, wordlist, output):
    if domain:
        domains = [domain]
    else:
        with open(domains) as domains_file:
            domains = domains_file.read().splitlines()

    with open(wordlist) as wordlist_file:
        wordlist = wordlist_file.read().splitlines()

    result = set()
    for domain in domains:
        result.update(generate_permutations(domain, wordlist))

    with open(output, "w") as output_file:
        output_file.write("\n".join(sorted(result)))


if __name__ == "__main__":
    main()
