import json
import os
import time

import boto3
import openai
from slack_bolt import App


ssm = boto3.client('ssm', region_name='ap-northeast-1')
app = App(
    token=ssm.get_parameter(
        Name="SLACK_BOT_TOKEN", WithDecryption=True
    )['Parameter']['Value'],
    signing_secret=ssm.get_parameter(
        Name="SLACK_SIGNING_SECRET", WithDecryption=True
    )['Parameter']['Value'],
    process_before_response=True,
)


class SlackMessageBuffer:
    UPDATE_INTERVAL = 0.5

    def __init__(self):
        self.last_updated_time = time.time()
        self.chunks_queue = []

    def enqueue_chunk(self, chunk):
        self.chunks_queue.append(chunk)

    def dequeue_all(self):
        chunks = "".join(self.chunks_queue)
        self.chunks_queue.clear()
        return chunks

    def is_interval_over(self):
        current_time = time.time()
        return current_time - self.last_updated_time > self.UPDATE_INTERVAL

    def reset_interval(self):
        self.last_updated_time = time.time()


def set_openai_messages(input_text):
    """OpenAI API に送信するメッセージリストをセット"""
    return [
        {"role": "system", "content": "あなたは優秀なアシスタントです。"},
        {"role": "user", "content": input_text}
    ]


def generate_openai_response(user_message):
    """OpenAI API からのストリーミングレスポンスを生成（yield で返す）"""
    openai.api_key = ssm.get_parameter(
        Name="OPENAI_API_KEY", WithDecryption=True
    )['Parameter']['Value']
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        stream=True,
        messages=set_openai_messages(user_message)
    )

    for chunk in response:
        yield chunk['choices'][0]['delta'].get('content', '')


# slackに返信。
# LLMの回答生成に時間がかかるので、回答中の内容を徐々にSlackへ送る
# 既存のメッセージを複数回更新する
# Streamingで取得したチャンクごとにSlackへ送ると、Slackの処理が遅くなるので、0.5秒インターバルでバッファーして送る
# チャンクされたテキストを結合する際に、毎回加算してもいいのだが、listのjoinで書くほうが処理が早いので、無駄に頑張った。
# 以下Slack上の表示されるテキストの例
# 0秒：AIが回答を作成中
# 0.5秒後：abc
# 1秒後：abcdef
# 1.5秒後：abcdefghij
def send_message_to_slack(channel_id, user_message, timestamp):
    print("start send_message_to_slack")

    buffer = SlackMessageBuffer()
    reply_text_in_progress = ""
    for chunk in generate_openai_response(user_message):

        if not chunk:
            continue

        buffer.enqueue_chunk(chunk)

        if buffer.is_interval_over():
            reply_text_in_progress += buffer.dequeue_all()
            app.client.chat_update(
                channel=channel_id, ts=timestamp, text=reply_text_in_progress
            )
            buffer.reset_interval()

    # 残りのチャンクを送信
    if buffer.chunks_queue:
        full_reply_content = reply_text_in_progress + buffer.dequeue_all()
        app.client.chat_update(
            channel=channel_id, ts=timestamp, text=full_reply_content
        )


# Lambdaイベントハンドラー
def lambda_handler(event, context):
    print("start lambda_handler")
    print(event)

    # SQSから情報を取り出す。
    body = json.loads(event["Records"][0]["body"])
    channel_id = body.get("channel_id")
    user_message = body.get("user_message")
    timestamp = body.get("timestamp")

    send_message_to_slack(channel_id, user_message, timestamp)
