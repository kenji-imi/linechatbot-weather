#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import sys
import requests

app = Flask(__name__)

#環境変数の取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', None)
YJDN_APP_ID = os.getenv('YJDN_APP_ID', None)
if LINE_CHANNEL_ACCESS_TOKEN is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)
if LINE_CHANNEL_SECRET is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if YJDN_APP_ID is None:
    print('Specify YJDN_APP_ID as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 入力された文字列を格納
    push_text = event.message.text
    app.logger.info("Recieved message:" + push_text)

    # リプライする文字列
    if push_text == "天気":
        reply_text = request_yahoo_weather()
    else:
        reply_text = push_text

    # リプライ部分の記述
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


def request_yahoo_weather():
    BASE_URL = "http://weather.olp.yahooapis.jp/v1/place"
    COORDINATES = "139.75358630,35.69404120"
    OUTPUT = "json"

    url = BASE_URL + "?appid=%s&coordinates=%s&output=%s" % (YJDN_APP_ID, COORDINATES, OUTPUT)
    response = requests.get(url).json()

    talk_text = ""

    talk_text += "[千代田区のこれから1時間の天気]" + "\n"
    for var in range(0, 7):
        rainfall = response['Feature'][0]['Property']['WeatherList']['Weather'][var]['Rainfall']
        type = response['Feature'][0]['Property']['WeatherList']['Weather'][var]['Type']

        rain_level = ""
        talk = ""
        if (rainfall == 0.0):
            rain_level = "雨は降"
        elif (rainfall < 5.0):
            rain_level = "雨がちょっと降"
        elif (rainfall < 10.0):
            rain_level = "雨が結構降"
        elif (rainfall < 20.0):
            rain_level = "やや強い雨が降"
        elif (rainfall < 30.0):
            rain_level = "土砂降りの雨が降"
        elif (rainfall < 50.0):
            rain_level = "激しい雨が降"
        elif (rainfall < 80.0):
            rain_level = "非常に激しい雨が降"
        elif (rainfall >= 80.0):
            rain_level = "猛烈な雨が降"

        if type == "observation":
            time = "今、"
            if rainfall == 0.0:
                suffix = "っていません"
                talk = time + rain_level + suffix
            else:
                suffix = "っています"
                talk = time + rain_level + suffix
        else:
            time = str(var * 10) + "分後、"
            if rainfall == 0.0:
                suffix = "りません"
            else:
                suffix = "りそうです"
            talk = time + rain_level + suffix
        talk_text += talk + "\n"

    return talk_text


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
