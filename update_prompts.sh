#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Activated virtual environment"
fi

# Run the Python script to update prompts
echo "Updating prompts using OpenAI..."
python update_prompts.py "$@"

echo "Done!" 