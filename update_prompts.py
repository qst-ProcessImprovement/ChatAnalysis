import os
import argparse
import sys
from openai import OpenAI
from dotenv import load_dotenv

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Update prompts using OpenAI')
    parser.add_argument('instruction', nargs='?', default=None,
                        help='Instruction for prompt modification (e.g., "要約が少々長いので、1・2行となるようにしてほしい")')
    args = parser.parse_args()

    # Check if instruction is provided
    if args.instruction is None:
        print("Error: No instruction provided.")
        print("Usage: python update_prompts.py \"修正指示\"")
        sys.exit(1)
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get OpenAI API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please make sure your .env file contains a valid API key.")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Fixed values
    model = "gpt-4o-mini"
    prompt_file = "emotion_analysis_prompt.txt"
    
    # Read the current prompt content
    try:
        if os.path.exists(prompt_file):
            with open(prompt_file, "r") as file:
                current_emotion_prompt = file.read().strip()
        else:
            # If the file doesn't exist yet, try to extract from prompts.py
            with open("prompts.py", "r") as file:
                prompts_content = file.read()
            
            # Extract current emotion prompt from prompts.py
            lines = prompts_content.split('\n')
            emotion_prompt_lines = []
            capturing = False
            
            for line in lines:
                if 'EMOTION_ANALYSIS_PROMPT = """' in line:
                    capturing = True
                    continue
                elif capturing and '"""' in line:
                    capturing = False
                    continue
                elif capturing:
                    emotion_prompt_lines.append(line)
            
            current_emotion_prompt = '\n'.join(emotion_prompt_lines).strip()
            
            if not current_emotion_prompt:
                raise ValueError("Could not extract emotion analysis prompt")
    except Exception as e:
        print(f"Error reading prompt file: {e}")
        return
    
    # Update emotion analysis prompt
    print(f"Updating emotion analysis prompt using {model} with instruction: {args.instruction}")
    new_emotion_prompt = update_prompt(client, model, "emotion analysis", current_emotion_prompt, args.instruction)
    
    if new_emotion_prompt:
        # Save the updated prompt to the txt file
        with open(prompt_file, "w") as file:
            file.write(new_emotion_prompt)
        
        print(f"Successfully updated {prompt_file}")
        
        # Create a new branch and commit the changes
        create_branch_and_commit(prompt_file, args.instruction)
    else:
        print(f"Failed to update {prompt_file}")

def update_prompt(client, model, prompt_type, current_prompt, instruction):
    """
    Update a prompt using OpenAI.
    
    Args:
        client: OpenAI client
        model: Model to use
        prompt_type: Type of prompt (emotion analysis)
        current_prompt: Current prompt text
        instruction: Instruction for prompt modification
        
    Returns:
        Updated prompt text or None if there was an error
    """
    try:
        system_message = f"""You are an expert at creating effective prompts for AI language models.
        Your task is to modify the existing {prompt_type} prompt according to this instruction: {instruction}.
        
        The prompt should:
        1. Keep the same general purpose and output format
        2. Preserve the original language (Japanese)
        3. Potentially improve clarity, specificity, or effectiveness
        
        Return ONLY the improved prompt text, without any explanations or additional text.
        Do NOT include any placeholders like {{date}} or {{messages}} in your response.
        """
        
        user_message = f"""Here is the current {prompt_type} prompt:
        
{current_prompt}
        
Please modify this prompt according to this instruction: {instruction}."""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        )
        
        new_prompt = response.choices[0].message.content.strip()
        return new_prompt
        
    except Exception as e:
        print(f"Error when calling OpenAI API: {e}")
        return None

def create_branch_and_commit(prompt_file, instruction):
    """
    Create a new branch, commit the changes, and push to remote.
    
    Args:
        prompt_file: The file that was updated
        instruction: Instruction used for modification
    """
    try:
        # Create a new branch
        branch_name = f"update-prompts-{os.popen('date +%Y%m%d%H%M%S').read().strip()}"
        os.system(f"git checkout -b {branch_name}")
        
        # Create commit message
        commit_message = f'Update emotion analysis prompt with instruction: "{instruction}"'
        pr_title = "Update emotion analysis prompt with custom instruction"
        pr_body = f'This PR updates the emotion analysis prompt using OpenAI with the instruction: "{instruction}".'
        
        # Commit the changes
        os.system(f"git add {prompt_file}")
        os.system(f'git commit -m "{commit_message}"')
        
        # Push the branch
        os.system(f"git push origin {branch_name}")
        
        # Create a pull request if GitHub CLI is available
        if os.system("command -v gh &> /dev/null") == 0:
            # Escape quotes in PR body for shell command
            escaped_pr_body = pr_body.replace('"', '\\"')
            os.system(f'gh pr create --title "{pr_title}" --body "{escaped_pr_body}"')
        else:
            print(f"GitHub CLI (gh) is not installed. Please create a pull request manually for branch {branch_name}.")
        
        print("Successfully created branch, committed changes, and pushed to remote.")
        
    except Exception as e:
        print(f"Error creating branch and committing changes: {e}")

if __name__ == "__main__":
    main() 