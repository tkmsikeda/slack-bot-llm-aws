import json
import os
import re

import boto3
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

sqs = boto3.client("sqs", region_name='ap-northeast-1')
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


# LLMの回答後に、「AIが回答を作成中」のメッセージを更新する用途
# 該当のメッセージを特定できる情報としてチャンネルIDとタイムスタンプを取得。
def extract_slack_message_info(say_response):
    channel_id = say_response["channel"]
    timestamp = say_response["ts"]
    return channel_id, timestamp


# Slackから送られてくる、ユーザのメッセージを抽出する。メンションを除去する。
def extract_message_from_slack_event(event):
    return re.sub(r"<@\w+>", "", event["text"]).strip()


# この関数では、Slackからのメンションをトリガーに、「とりあえずの一言応答」と「SQSへ必要情報を引き継ぐ」処理を実施。
# SlackAPIは3秒以内に202OKを返さないと再送して複数回Lambdaが実行される。
# LLMは回答生成完了までに3秒以上かかってしまうため、Slackの仕様で再送が発生する。
# 複数回のlambda実行を防ぐために「LLMが生成した内容をSlackへの返信する処理」は、非同期で実施する。
@app.event("app_mention")
def handle_mention(event, say):
    # TODO loggerに変える
    print("start app_menstion")
    print(event)

    # 即時応答メッセージ
    say_response = say(text="AIが回答を作成中")
    print("say:", say_response)

    # SQSへ必要情報を引き継ぐ
    channel_id, timestamp = extract_slack_message_info(say_response)
    message_from_slack = extract_message_from_slack_event(event)
    sqs.send_message(
        QueueUrl=ssm.get_parameter(
            Name="SQS_QUEUE_URL", WithDecryption=True
        )['Parameter']['Value'],
        MessageBody=json.dumps({
            "channel_id": channel_id,
            "user_message": message_from_slack,
            "timestamp": timestamp,
        }),
    )


# Lambdaイベントハンドラー
def lambda_handler(event, context):
    print("start lambda_handler")
    print(event)
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
