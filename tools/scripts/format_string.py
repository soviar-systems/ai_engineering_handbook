#!/usr/bin/env python3

import argparse
import re


def main():
    parser = argparse.ArgumentParser(
        description="Format a string to be URL-safe and filesystem-friendly."
    )
    parser.add_argument("input_string", help="The string to format")
    parser.add_argument(
        "--trunc", action="store_true", help="Enable truncation (off by default)"
    )
    parser.add_argument(
        "--trunc-len",
        type=int,
        default=50,
        help="Maximum length when truncation is enabled (default: 50)",
    )
    args = parser.parse_args()
    print(format_string(args.input_string, trunc=args.trunc, trunc_len=args.trunc_len))


def format_string(input_string, trunc: bool = False, trunc_len: int = 50):
    """
    Format the input string to be URL-safe and filesystem-friendly.

    Args:
    input_string (str): The string to be formatted.

    Returns:
    str: The formatted string.
    """

    # Strip known file extensions
    # Compound extensions first (longest match wins), then simple
    extensions_to_strip = [
        ".tar.gz", ".tar.bz2", ".tar.xz",
        ".pdf", ".epub", ".html", ".htm", ".txt", ".md",
        ".ipynb", ".doc", ".docx", ".odt", ".rtf", ".csv",
        ".json", ".yaml", ".yml", ".xml", ".png", ".jpg",
        ".jpeg", ".gif", ".svg", ".mp3", ".mp4", ".wav",
        ".zip", ".gz", ".bz2", ".xz", ".7z", ".rar", ".tar",
    ]
    for ext in extensions_to_strip:
        if input_string.lower().endswith(ext):
            input_string = input_string[: -len(ext)]
            break

    # Convert to lowercase
    formatted_string = input_string.lower()

    # Replace & with and
    formatted_string = formatted_string.replace("&", "and")

    # List of special symbols to remove
    special_symbols_to_remove = [
        "the ",
        "(",
        ")",
        "# ",
        "#",
        "`",
        "~",
        "$",
        "%",
        "@",
        '"',
        "“",
        "”",
        "'",
        "’",
    ]
    for s in special_symbols_to_remove:
        formatted_string = formatted_string.replace(s, "")

    # List of special symbols to replace with "_"
    special_symbols_to_replace = [
        '"',
        "'",
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
        "—",
        "–",
    ]
    replace_pattern = "|".join(map(re.escape, special_symbols_to_replace))
    formatted_string = re.sub(rf"\s*({replace_pattern})\s*", "_", formatted_string)

    # Replace multiple underscores with a single underscore
    formatted_string = re.sub(r"_+", "_", formatted_string).strip("_")

    # Replace spaces with underscores for URL safety
    formatted_string = formatted_string.replace(" ", "_")

    # Truncate the string if it exceeds trunc_len characters
    if trunc:
        if len(formatted_string) > trunc_len:
            formatted_string = formatted_string[:trunc_len]

    if formatted_string[-1] == "_":
        formatted_string = formatted_string[:-1]

    return formatted_string


if __name__ == "__main__":
    main()
