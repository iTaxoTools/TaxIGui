#!/usr/bin/env python3

import sys
from random import choices, randint


def fetch(list, index, default):
    try:
        return list[index]
    except IndexError:
        return default


def sequence(low=10, high=10):
    return "".join(choices("AGCT-", k=randint(low, high)))


def main():
    sample_count = int(fetch(sys.argv, 1, randint(10, 20)))
    sample_length_min = int(fetch(sys.argv, 2, randint(10, 20)))
    sample_length_max = int(
        fetch(sys.argv, 3, randint(sample_length_min, sample_length_min + 10))
    )
    sample_prefix = fetch(sys.argv, 4, "sample")

    print("seqid\tspecimen_voucher\torganism\tsequence", end="")
    print()
    for sample in range(sample_count):
        print(f"{sample_prefix}_{str(sample)}", end="")
        print(f"\tvoucher_{str(sample)}", end="")
        print(f"\torganism_{str(sample)}", end="")
        print(f"\t{sequence(sample_length_min, sample_length_max)}", end="")
        print()


if __name__ == "__main__":
    main()
