import os
import logging
import re
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Any, Union

from openai import OpenAI
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Conditionally load environment variables from .env file when running locally
try:
    from dotenv import load_dotenv
    # Check if .env file exists before loading
    if os.path.exists('.env'):
        load_dotenv()
        print("Loaded environment variables from .env file")
except ImportError:
    # dotenv package not installed, assuming running in GitHub Actions
    pass

# Required environment variables:
# - OPENAI_API_KEY
# - SLACK_API_TOKEN
# - SOURCE_CHANNEL_ID
# - TARGET_CHANNEL_ID
# 
# These can be set in:
# 1. A .env file (for local development, not committed to Git)
# 2. GitHub Actions environment variables (for CI/CD workflows)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Debug file paths
DEBUG_CONVERSATION_FILE = "debug/conversation_history.txt"
DEBUG_RESULT_FILE = "debug/result.txt"

# Hardcoded emotion analysis prompt
EMOTION_ANALYSIS_PROMPT_CORE = """これらのメッセージからユーザーの感情状態を簡潔に分析してください。
ポジティブな感情、ネガティブな感情、中立的な感情などを特定し、
その日のユーザーの全体的な感情状態を3-5文程度で簡潔に要約してください。
冗長な説明は避け、要点のみを述べてください。"""


class OpenAIClient:
    """Class to handle interactions with OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key. If None, will be loaded from environment variable.
            model: The model to use for chat completions.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
    
    def chat_completion(self, message: str, system_prompt: str = "You are a helpful assistant.") -> str:
        """
        Send a message to the model and get a response.
        
        Args:
            message: The message to send to the model.
            system_prompt: The system prompt to use.
            
        Returns:
            The model's response text.
            
        Raises:
            Exception: If there's an error communicating with the OpenAI API.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error communicating with OpenAI API: {e}")
            raise


class SlackClient:
    """Class to handle interactions with Slack API."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Slack client.
        
        Args:
            token: Slack API token. If None, will be loaded from environment variable.
        """
        self.token = token or os.getenv("SLACK_API_TOKEN")
        if self.token:
            self.client = WebClient(token=self.token)
    
    def fetch_conversation_history(self, channel_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch conversation history from a Slack channel.
        
        Args:
            channel_id: The ID of the Slack channel.
            
        Returns:
            List of message dictionaries from Slack API, or None if there was an error.
        """
        if not self.token:
            return None
            
        try:
            result = self.client.conversations_history(channel=channel_id)
            conversation_history = result["messages"]
            
            logger.info(f"{len(conversation_history)} messages found in {channel_id}")
            return conversation_history
        
        except SlackApiError as e:
            logger.error(f"Error fetching conversation history from Slack: {e}")
            return None
    
    def post_message(self, channel_id: str, text: str) -> bool:
        """
        Post a message to a Slack channel.
        
        Args:
            channel_id: The ID of the Slack channel.
            text: The message text to post.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.token:
            return False
            
        try:
            self.client.chat_postMessage(
                channel=channel_id,
                text=text
            )
            
            logger.info(f"Message posted to Slack channel {channel_id}")
            return True
        
        except SlackApiError as e:
            logger.error(f"Error posting message to Slack: {e}")
            return False
    
    def upload_file(self, channel_id: str, file_path: str, title: str, 
                   initial_comment: str = "") -> bool:
        """
        Upload a file to a Slack channel.
        
        Args:
            channel_id: The ID of the Slack channel.
            file_path: Path to the file to upload.
            title: Title for the file.
            initial_comment: Initial comment for the file.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.token:
            return False
            
        try:
            self.client.files_upload_v2(
                channels=channel_id,
                title=title,
                file=file_path,
                initial_comment=initial_comment
            )
            
            logger.info(f"File uploaded to Slack channel {channel_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error uploading file to Slack: {e}")
            return False


class MessageFormatter:
    """Class to handle formatting and parsing of messages."""
    
    @staticmethod
    def format_slack_messages(messages: List[Dict[str, Any]]) -> str:
        """
        Format Slack messages into a text format for analysis.
        
        Args:
            messages: List of message dictionaries from Slack API.
            
        Returns:
            Formatted conversation text.
        """
        formatted_messages = []
        
        for message in messages:
            # Skip messages without 'user' or 'ts' fields
            if 'user' not in message or 'ts' not in message:
                continue
                
            # Convert timestamp to readable format
            timestamp = float(message['ts'])
            readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            # Format the message
            formatted_message = f"{message['user']}: {message.get('text', '')} (timestamp: {readable_time})"
            formatted_messages.append(formatted_message)
        
        return "\n".join(formatted_messages)
    
    @staticmethod
    def read_conversation_from_file(file_path: str) -> str:
        """
        Read conversation history from a file.
        
        Args:
            file_path: Path to the file containing conversation history.
            
        Returns:
            The conversation history as a string.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                conversation_text = file.read()
            
            return conversation_text
        except Exception as e:
            logger.error(f"Error reading conversation history from file: {e}")
            return ""
    
    @staticmethod
    def parse_conversations_by_date(conversation_text: str) -> Dict[str, List[str]]:
        """
        Parse the conversation text and group messages by date.
        
        Args:
            conversation_text: The conversation history text.
            
        Returns:
            A dictionary with dates as keys and lists of messages as values.
        """
        # Regex pattern to match the format: "U08BTPRSAHZ: message content (timestamp: 2025-02-28 07:57:11)"
        pattern = r'([A-Z0-9]+):\s+(.*?)\s+\(timestamp:\s+(\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}:\d{2}\)'
        
        conversations_by_date = defaultdict(list)
        
        # Find all matches in the text
        matches = re.findall(pattern, conversation_text, re.DOTALL)
        
        for user_id, message, date_str in matches:
            # Create a formatted message with user ID
            formatted_message = f"{user_id}: {message.strip()}"
            conversations_by_date[date_str].append(formatted_message)
        
        return conversations_by_date
    
    @staticmethod
    def format_analysis_results(emotion_analysis: Dict[str, str], trend_analysis: str = None) -> str:
        """
        Format the emotion analysis results into a text format.
        
        Args:
            emotion_analysis: Dictionary with dates as keys and emotion analysis as values.
            trend_analysis: Analysis of emotion trends over time. Defaults to None and is not used.
            
        Returns:
            Formatted analysis results.
        """
        content = "=== 日付ごとの感情分析 ===\n"
        
        for date in sorted(emotion_analysis.keys()):
            content += f"\n日付: {date}\n"
            content += f"{emotion_analysis[date]}\n"
        
        return content


class EmotionAnalyzer:
    """Class to handle emotion analysis of conversations."""
    
    def __init__(self, openai_client: OpenAIClient):
        """
        Initialize the emotion analyzer.
        
        Args:
            openai_client: OpenAI client for API interactions.
        """
        self.openai_client = openai_client
    
    def analyze_emotions_by_date(self, conversations_by_date: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Analyze emotions in conversations grouped by date.
        
        Args:
            conversations_by_date: Dictionary with dates as keys and lists of messages as values.
            
        Returns:
            A dictionary with dates as keys and emotion analysis as values.
        """
        emotion_analysis = {}
        
        for date, messages in conversations_by_date.items():
            # Combine messages for this date
            combined_messages = "\n".join(messages)
            
            # Create a prompt for emotion analysis
            prompt = self._create_emotion_analysis_prompt(date, combined_messages)
            
            # Get analysis from OpenAI
            try:
                analysis = self.openai_client.chat_completion(prompt)
                emotion_analysis[date] = analysis
                
                # Log progress
                logger.info(f"Analyzed emotions for date: {date}")
            except Exception as e:
                logger.error(f"Error analyzing emotions for date {date}: {e}")
                emotion_analysis[date] = f"分析エラー: {e}"
        
        return emotion_analysis
    
    @staticmethod
    def _create_emotion_analysis_prompt(date: str, messages: str) -> str:
        """
        Create a prompt for emotion analysis.
        
        Args:
            date: The date of the messages.
            messages: The combined messages for the date.
            
        Returns:
            A prompt for emotion analysis.
        """
        return f"""以下は特定の日付（{date}）のチャットメッセージです。
{EMOTION_ANALYSIS_PROMPT_CORE}

メッセージ:
{messages}
"""


class ResultsHandler:
    """Class to handle saving and posting of analysis results."""
    
    def __init__(self, slack_client: Optional[SlackClient] = None):
        """
        Initialize the results handler.
        
        Args:
            slack_client: Slack client for API interactions.
        """
        self.slack_client = slack_client
    
    def save_to_file(self, content: str, output_file: str) -> bool:
        """
        Save content to a file.
        
        Args:
            content: The content to save.
            output_file: Path to the output file.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(content)
            
            return True
        except Exception as e:
            logger.error(f"Error saving results to file: {e}")
            return False
    
    def post_to_slack(self, content: str, channel_id: str) -> bool:
        """
        Post content to a Slack channel.
        
        Args:
            content: The content to post.
            channel_id: The ID of the Slack channel.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.slack_client:
            return False
        
        return self.slack_client.post_message(channel_id, content)
    
    def post_as_file_to_slack(self, content: str, channel_id: str, 
                             file_name: str = "analysis_results.txt",
                             title: str = "感情分析結果",
                             comment: str = "チャット履歴の感情分析結果:") -> bool:
        """
        Post content as a file to a Slack channel.
        
        Args:
            content: The content to post.
            channel_id: The ID of the Slack channel.
            file_name: Name for the temporary file.
            title: Title for the file.
            comment: Initial comment for the file.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.slack_client:
            return False
        
        try:
            # Create a temporary file
            temp_file_path = file_name
            with open(temp_file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            # Upload the file to Slack
            result = self.slack_client.upload_file(
                channel_id=channel_id,
                file_path=temp_file_path,
                title=title,
                initial_comment=comment
            )
            
            # Remove the temporary file
            os.remove(temp_file_path)
            
            return result
        
        except Exception as e:
            logger.error(f"Error posting results file to Slack: {e}")
            return False


class ChatAnalysisApp:
    """Main application class for chat analysis."""
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialize the chat analysis application.
        
        Args:
            config: Configuration dictionary with API keys and channel IDs.
                   If None, will be loaded from environment variables.
                   Environment variables can be set in a .env file (for local development)
                   or in GitHub Actions (for CI/CD workflows).
        """
        self.config = config or {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "slack_api_token": os.getenv("SLACK_API_TOKEN"),
            "source_channel_id": os.getenv("SOURCE_CHANNEL_ID"),
            "target_channel_id": os.getenv("TARGET_CHANNEL_ID")
        }
        
        # Check if we're in debug mode (any required key is missing)
        required_keys = ["openai_api_key", "slack_api_token", "source_channel_id", "target_channel_id"]
        missing_keys = [key for key in required_keys if not self.config.get(key)]
        
        self.debug_mode = len(missing_keys) > 0
        
        # Initialize OpenAI client
        try:
            self.openai_client = OpenAIClient(api_key=self.config.get("openai_api_key"))
        except ValueError:
            self.openai_client = None
        
        # Initialize Slack client (optional in debug mode)
        self.slack_client = SlackClient(token=self.config.get("slack_api_token"))
        
        # Initialize components
        self.formatter = MessageFormatter()
        if self.openai_client:
            self.analyzer = EmotionAnalyzer(openai_client=self.openai_client)
        else:
            self.analyzer = None
        self.results_handler = ResultsHandler(slack_client=self.slack_client)
    
    def run(self) -> bool:
        """
        Run the chat analysis process.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get conversation data (from Slack or debug file)
            conversations_by_date = self._get_conversation_data()
            
            if not conversations_by_date:
                return False
            
            # Check if we can perform analysis
            if not self.analyzer:
                # If we can't analyze, but we have conversation data, just save the raw data
                if self.debug_mode and conversations_by_date:
                    raw_content = self._format_raw_conversations(conversations_by_date)
                    success = self.results_handler.save_to_file(raw_content, DEBUG_RESULT_FILE)
                    if success:
                        print(f"会話データをファイル {DEBUG_RESULT_FILE} に保存しました。")
                    return success
                return False
            
            # Analyze emotions
            emotion_analysis = self.analyzer.analyze_emotions_by_date(conversations_by_date)
            
            # Format results (トレンド分析を行わない)
            results_content = self.formatter.format_analysis_results(emotion_analysis)
            
            # Output results (to Slack or debug file)
            success = self._output_results(results_content)
            
            return success
        
        except Exception as e:
            logger.error(f"Error running chat analysis: {e}")
            return False
    
    def _get_conversation_data(self) -> Dict[str, List[str]]:
        """
        Get conversation data from Slack or debug file.
        
        Returns:
            Dictionary with dates as keys and lists of messages as values.
        """
        if self.debug_mode:
            # Read from debug file
            conversation_text = self.formatter.read_conversation_from_file(DEBUG_CONVERSATION_FILE)
            if not conversation_text:
                return {}
        else:
            # Fetch from Slack
            slack_messages = self.slack_client.fetch_conversation_history(self.config["source_channel_id"])
            
            if not slack_messages:
                return {}
            
            # Format the messages for analysis
            conversation_text = self.formatter.format_slack_messages(slack_messages)
        
        # Parse conversations by date
        conversations_by_date = self.formatter.parse_conversations_by_date(conversation_text)
        
        return conversations_by_date
    
    def _format_raw_conversations(self, conversations_by_date: Dict[str, List[str]]) -> str:
        """
        Format raw conversation data for output when analysis is not possible.
        
        Args:
            conversations_by_date: Dictionary with dates as keys and lists of messages as values.
            
        Returns:
            Formatted conversation text.
        """
        content = "=== 日付ごとの会話データ ===\n"
        
        for date in sorted(conversations_by_date.keys()):
            content += f"\n日付: {date}\n"
            content += "\n".join(conversations_by_date[date])
            content += "\n"
        
        return content
    
    def _output_results(self, results_content: str) -> bool:
        """
        Output results to Slack or debug file.
        
        Args:
            results_content: Formatted analysis results.
            
        Returns:
            True if successful, False otherwise.
        """
        if self.debug_mode:
            # Save to debug file
            success = self.results_handler.save_to_file(results_content, DEBUG_RESULT_FILE)
            
            if success:
                print(f"感情分析の結果をファイル {DEBUG_RESULT_FILE} に保存しました。")
            
            return success
        else:
            # Post to Slack
            success = self.results_handler.post_to_slack(
                results_content, 
                self.config["target_channel_id"]
            )
            
            if success:
                print(f"感情分析の結果をSlackチャンネル {self.config['target_channel_id']} に投稿しました。")
            
            return success


def main():
    """Main entry point for the application."""
    try:
        # Set the current working directory to the module's folder
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Log the source of environment variables
        if os.path.exists('.env'):
            logger.info("Using environment variables from .env file for API keys and channel IDs")
        else:
            logger.info("Using environment variables from system environment (GitHub Actions) for API keys and channel IDs")
        
        # Create and run the application
        app = ChatAnalysisApp()
        success = app.run()
        
        return 0 if success else 1
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
    