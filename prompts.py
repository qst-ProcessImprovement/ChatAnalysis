"""
This module contains prompts used for emotion analysis in the chat analysis application.
These prompts can be modified without changing the main application code.
"""

# Prompt for analyzing emotions in messages for a specific date
EMOTION_ANALYSIS_PROMPT = """
以下は特定の日付（{date}）のチャットメッセージです。
これらのメッセージからユーザーの感情状態を簡潔に分析してください。
ポジティブな感情、ネガティブな感情、中立的な感情などを特定し、
その日のユーザーの全体的な感情状態を3-5文程度で簡潔に要約してください。
冗長な説明は避け、要点のみを述べてください。

メッセージ:
{messages}
"""

# Prompt for analyzing trends in emotions over time
TREND_ANALYSIS_PROMPT = """
以下は日付ごとの感情分析結果です。これらの結果を時系列で分析し、
感情の変化や傾向、パターンを特定してください。
特に注目すべき変化や転換点があれば強調してください。
分析は簡潔に、5-7文程度にまとめてください。冗長な説明は避け、要点のみを述べてください。

{all_analyses}
""" 