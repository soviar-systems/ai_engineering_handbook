# README: Instructions to Run the Script `format_string.py`

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.2.1  
Birth: 2025-12-20  
Last Modified: 2025-12-20

-----

The purpose of the script is to convert a given input string into a formatted version by performing the following operations:

1. **Remove Colons**: It removes all colons (`:`) from the string.
2. **Remove Double Quotes**: It removes all double quotes (`"`) from the string.
3. **Replace Spaces with Underscores**: It replaces all spaces (` `) in the string with underscores (`_`).
4. **Convert to Lowercase**: It converts the entire string to lowercase.

This script is designed to be run from the Linux terminal, allowing you to pass any string as an argument and receive the formatted output directly in the terminal. This can be particularly useful for standardizing text formats, such as creating file names or identifiers that follow specific naming conventions.

1. Make the Script Executable

Open your terminal and navigate to the directory where you saved the script. Run the following command to make the script
executable:

```bash
chmod +x format_string.py
```

2. Run the Script

Execute the script by passing the string you want to format as an argument. For example:

```bash
./format_string.py 'Agents4Science Conference Paper Digest: How Agents Are "Doing" Science Right Now'
```

This will output:

```
agents4science_conference_paper_digest_how_agents_are_doing_science_right_now
```

You can now use this script to format any string from the terminal.
