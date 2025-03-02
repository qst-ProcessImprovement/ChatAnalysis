# Chat Analysis

チャット分析ツールは、Slackの会話履歴から感情分析を行い、その結果をSlackチャンネルに投稿するPythonアプリケーションです。

## 機能

- Slack APIを使用して特定のチャンネルから会話履歴を取得
- OpenAI APIを使用して会話の感情分析を実行
- 日付ごとに会話を分類し、それぞれの日の感情状態を分析
- 分析結果をSlackチャンネルに投稿または指定されたファイルに保存
- デバッグモードでローカルファイルからの会話履歴の読み込みをサポート

## 必要条件

- Python 3.6以上
- 以下のPythonパッケージ:
  - openai
  - slack_sdk
  - python-dotenv

## インストール

1. リポジトリをクローン:
```bash
git clone https://github.com/yourusername/chat_analysis.git
cd chat_analysis
```

2. 必要なパッケージをインストール:
```bash
pip install -r requirements.txt
```

3. `.env`ファイルを作成し、必要な環境変数を設定:
```
OPENAI_API_KEY=your_openai_api_key
SLACK_API_TOKEN=your_slack_api_token
SOURCE_CHANNEL_ID=source_channel_id
TARGET_CHANNEL_ID=target_channel_id
```

## 使用方法

### 通常モード

すべての環境変数が正しく設定されている場合、以下のコマンドで実行できます:

```bash
python chat_analysis.py
```

このモードでは:
1. 指定されたソースチャンネルから会話履歴を取得
2. OpenAI APIを使用して感情分析を実行
3. 分析結果を指定されたターゲットチャンネルに投稿

### デバッグモード

必要な環境変数が設定されていない場合、アプリケーションは自動的にデバッグモードで動作します。このモードでは:

1. `debug/conversation_history.txt`から会話履歴を読み込み
2. OpenAI APIが利用可能な場合は感情分析を実行
3. 結果を`debug/result.txt`に保存

デバッグ用のファイルを準備するには:

1. `debug`ディレクトリを作成
2. `conversation_history.txt`ファイルを作成し、以下の形式で会話履歴を記述:
```
U12345: こんにちは (timestamp: 2023-01-01 12:34:56)
U67890: おはようございます (timestamp: 2023-01-01 12:35:10)
```

## プロジェクト構造

- `chat_analysis.py`: メインアプリケーションコード
- `requirements.txt`: 必要なPythonパッケージのリスト
- `.env`: 環境変数設定ファイル
- `debug/`: デバッグモード用のディレクトリ
  - `conversation_history.txt`: デバッグ用の会話履歴
  - `result.txt`: 分析結果の出力先

## クラス構造

- `OpenAIClient`: OpenAI APIとの対話を処理
- `SlackClient`: Slack APIとの対話を処理
- `MessageFormatter`: メッセージのフォーマットと解析を処理
- `EmotionAnalyzer`: 会話の感情分析を実行
- `ResultsHandler`: 分析結果の保存と投稿を処理
- `ChatAnalysisApp`: メインアプリケーションクラス

## ライセンス

[MIT](https://choosealicense.com/licenses/mit/) 