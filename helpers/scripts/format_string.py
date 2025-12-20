#!/usr/bin/env python3

import sys


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 format_string.py 'Your Input String'")
    else:
        input_str = sys.argv[1]
        formatted_str = format_string(input_str)
        print(formatted_str)


def format_string(input_string):
    # Remove colons, double quotes, and replace spaces with underscores
    formatted_string = (
        input_string.lower()
        .replace("the ", "")
        .replace(":", "")
        .replace('"', "")
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "_")
        .replace("-", "_")
    )
    return formatted_string


if __name__ == "__main__":
    main()
