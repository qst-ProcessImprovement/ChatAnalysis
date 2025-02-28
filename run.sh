#!/bin/bash

# Step 1: Create a new branch
git checkout -b new-branch-name

# Step 2: Add a line to the README
echo "abc" >> README.md

# Step 3: Commit and push the changes
git add README.md
git commit -m "Add 'abc' to README"
git push origin new-branch-name

# Step 4: Create a pull request
gh pr create --title "Add 'abc' to README" --body "This PR adds a line 'abc' to the README file."