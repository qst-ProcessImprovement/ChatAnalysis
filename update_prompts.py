import os
import re
import argparse
from openai import OpenAI
from dotenv import load_dotenv

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Update prompts using OpenAI')
    parser.add_argument('--prompt', choices=['emotion', 'trend', 'both'], default='both',
                        help='Which prompt to update: emotion, trend, or both')
    parser.add_argument('--model', default='gpt-4o-mini',
                        help='OpenAI model to use (default: gpt-4o-mini)')
    args = parser.parse_args()

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
    
    # Read the current prompts.py content
    try:
        with open("prompts.py", "r") as file:
            prompts_content = file.read()
    except FileNotFoundError:
        print("Error: prompts.py file not found.")
        return
    
    # Extract current prompts
    emotion_prompt_match = re.search(r'EMOTION_ANALYSIS_PROMPT\s*=\s*"""(.*?)"""', prompts_content, re.DOTALL)
    trend_prompt_match = re.search(r'TREND_ANALYSIS_PROMPT\s*=\s*"""(.*?)"""', prompts_content, re.DOTALL)
    
    if not emotion_prompt_match or not trend_prompt_match:
        print("Error: Could not find prompts in prompts.py")
        return
    
    current_emotion_prompt = emotion_prompt_match.group(1).strip()
    current_trend_prompt = trend_prompt_match.group(1).strip()
    
    # Update prompts based on command line arguments
    if args.prompt in ['emotion', 'both']:
        print(f"Updating emotion analysis prompt using {args.model}...")
        new_emotion_prompt = update_prompt(client, args.model, "emotion analysis", current_emotion_prompt)
        if new_emotion_prompt:
            prompts_content = prompts_content.replace(
                f'EMOTION_ANALYSIS_PROMPT = """{current_emotion_prompt}"""',
                f'EMOTION_ANALYSIS_PROMPT = """{new_emotion_prompt}"""'
            )
    
    if args.prompt in ['trend', 'both']:
        print(f"Updating trend analysis prompt using {args.model}...")
        new_trend_prompt = update_prompt(client, args.model, "trend analysis", current_trend_prompt)
        if new_trend_prompt:
            prompts_content = prompts_content.replace(
                f'TREND_ANALYSIS_PROMPT = """{current_trend_prompt}"""',
                f'TREND_ANALYSIS_PROMPT = """{new_trend_prompt}"""'
            )
    
    # Write the updated prompts back to the file
    with open("prompts.py", "w") as file:
        file.write(prompts_content)
    
    print("Successfully updated prompts.py")
    
    # Create a new branch and commit the changes
    create_branch_and_commit()

def update_prompt(client, model, prompt_type, current_prompt):
    """
    Update a prompt using OpenAI.
    
    Args:
        client: OpenAI client
        model: Model to use
        prompt_type: Type of prompt (emotion analysis or trend analysis)
        current_prompt: Current prompt text
        
    Returns:
        Updated prompt text or None if there was an error
    """
    try:
        system_message = f"""
        You are an expert at creating effective prompts for AI language models.
        Your task is to improve the existing {prompt_type} prompt while maintaining its core functionality.
        
        The prompt should:
        1. Be clear and concise
        2. Maintain all format placeholders (like {{date}}, {{messages}}, or {{all_analyses}})
        3. Preserve the original language (Japanese)
        4. Keep the same general purpose and output format
        5. Potentially improve clarity, specificity, or effectiveness
        
        Return ONLY the improved prompt text, without any explanations or additional text.
        """
        
        user_message = f"""
        Here is the current {prompt_type} prompt:
        
        {current_prompt}
        
        Please improve this prompt while maintaining its core functionality and format placeholders.
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        )
        
        new_prompt = response.choices[0].message.content.strip()
        
        # Verify that the placeholders are still present
        if prompt_type == "emotion analysis" and "{date}" not in new_prompt or "{messages}" not in new_prompt:
            print("Error: The updated emotion analysis prompt is missing required placeholders.")
            return None
        
        if prompt_type == "trend analysis" and "{all_analyses}" not in new_prompt:
            print("Error: The updated trend analysis prompt is missing required placeholders.")
            return None
        
        return new_prompt
        
    except Exception as e:
        print(f"Error when calling OpenAI API: {e}")
        return None

def create_branch_and_commit():
    """
    Create a new branch, commit the changes, and push to remote.
    """
    try:
        # Create a new branch
        branch_name = f"update-prompts-{os.popen('date +%Y%m%d%H%M%S').read().strip()}"
        os.system(f"git checkout -b {branch_name}")
        
        # Commit the changes
        os.system("git add prompts.py")
        os.system('git commit -m "Update prompts using OpenAI"')
        
        # Push the branch
        os.system(f"git push origin {branch_name}")
        
        # Create a pull request if GitHub CLI is available
        if os.system("command -v gh &> /dev/null") == 0:
            os.system('gh pr create --title "Update prompts using OpenAI" --body "This PR updates the prompts used for emotion and trend analysis using OpenAI."')
        else:
            print(f"GitHub CLI (gh) is not installed. Please create a pull request manually for branch {branch_name}.")
        
        print("Successfully created branch, committed changes, and pushed to remote.")
        
    except Exception as e:
        print(f"Error creating branch and committing changes: {e}")

if __name__ == "__main__":
    main() 