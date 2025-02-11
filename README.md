# このアプリのデモ動画

https://github.com/user-attachments/assets/1f67d4a9-257b-4eac-956e-0840720c20a9

* SlackのボットとしてOpenaiのGPTモデルと会話できます。
* 回答途中の内容を随時更新しながら、表示することで、回答の待ち時間を短縮しています。
* 以上のシンプルなアプリです。

# このアプリの実現方法
## アーキテクチャ
![image](https://github.com/user-attachments/assets/fca92e50-a89d-46e7-bc54-10e97cb08784)

* AWS上で動作しています。
* LLMの回答はOpenaiAPIを利用しています。


## シーケンス概要
* SlackAPI→APIGW→Lambda→SQS→Lambda→OpenaiAPI→SlackAPI
