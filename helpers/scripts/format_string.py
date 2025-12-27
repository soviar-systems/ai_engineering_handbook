#!/usr/bin/env python3

import re
import sys


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 format_string.py 'Your Input String'")
    else:
        input_str = sys.argv[1]
        print(format_string(input_str))


def format_string(input_string):
    """
    Format the input string to be URL-safe and filesystem-friendly.

    Args:
    input_string (str): The string to be formatted.

    Returns:
    str: The formatted string.
    """

    # Convert to lowercase
    formatted_string = input_string.lower()

    # Replace & with and
    formatted_string = formatted_string.replace("&", "and")

    # Remove parentheses
    formatted_string = formatted_string.replace("(", "").replace(")", "")

    # Remove or replace special symbols
    # List of special symbols to remove
    special_symbols_to_remove = [
        r"\bthe\b",
    ]
    remove_pattern = "|".join(map(re.escape, special_symbols_to_remove))
    formatted_string = re.sub(rf"\s*({remove_pattern})\s*", "", formatted_string)

    # List of special symbols to replace with "_"
    special_symbols_to_replace = [
        ".",
        ",",
        ";",
        ":",
        "!",
        "?",
        "-",
        "/",
        "\\",
        "|",
        "<",
        ">",
        "*",
    ]
    replace_pattern = "|".join(map(re.escape, special_symbols_to_replace))
    formatted_string = re.sub(rf"\s*({replace_pattern})\s*", "_", formatted_string)

    # Replace multiple underscores with a single underscore
    formatted_string = re.sub(r"_+", "_", formatted_string).strip("_")

    # Replace spaces with underscores for URL safety
    formatted_string = formatted_string.replace(" ", "_")

    return formatted_string


if __name__ == "__main__":
    main()
