#!/bin/bash

# Get the list of files that are staged for commit
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.md$')

if [ -z "$STAGED_FILES" ]; then
  echo "No markdown files staged for commit."
  exit 0
fi

# Run the check_broken_links.py script on each staged markdown file
for FILE in $STAGED_FILES; do
  python3 helpers/scripts/check_broken_links.py . "*.md" --exclude-dirs in_progress pr --exclude-files .aider.chat.history.md "$FILE"
  if [ $? -ne 0 ]; then
    echo "Broken links found in $FILE. Please fix them before committing."
    exit 1
  fi
done

exit 0
