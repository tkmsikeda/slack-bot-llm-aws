# このアプリのデモ動画

https://github.com/user-attachments/assets/1f67d4a9-257b-4eac-956e-0840720c20a9

* SlackのボットとしてOpenAIのGPTモデルと会話できます。
* 回答途中の内容を随時更新しながら、表示することで、回答の待ち時間を短縮しています。
* 以上のシンプルなアプリです。

# このアプリの実現方法
## アーキテクチャと処理概要
![image](https://github.com/user-attachments/assets/51ef55ce-8bab-4b94-a6ae-f13d7e3d2c65)


* AWS上で動作しています。
* LLMの回答はOpenAIAPIを利用しています。
* 処理フローについて
1. 一次回答
1.1 Slackに即時応答するために、回答生成中の旨を送信する
1.2 SlackからのレスポンスのチャンネルIDとタイムスタンプを取得する
    3. 非同期で引き継ぎ
    4. 回答取得
    5. 回答送信


## シーケンス概要
* SlackAPI→APIGW→Lambda→SQS→Lambda→OpenaiAPI→SlackAPI
