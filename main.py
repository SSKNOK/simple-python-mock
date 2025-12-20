from flask import Flask, request, jsonify
import logging
import os
from datetime import datetime
from logging import StreamHandler, FileHandler, Formatter
from logging import INFO, DEBUG, NOTSET
import json
import re

"""
パス一致チェック（正規表現）
"""
def is_same_path(request_path, mock_path):
    pattern = re.compile(mock_path)
    return bool(pattern.match(request_path))

app = Flask(__name__)

########################################################
# ログの設定
########################################################
# ストリームハンドラの設定
stream_handler = StreamHandler()
stream_handler.setLevel(INFO)
stream_handler.setFormatter(Formatter("%(message)s"))
# 保存先の有無チェック
if not os.path.isdir('./log'):
    os.makedirs('./log', exist_ok=True)
# ファイルハンドラの設定
file_handler = FileHandler(
    f"./Log/log{datetime.now():%Y%m%d%H%M%S}.log"
)
# ログ出力設定
file_handler.setLevel(DEBUG)
file_handler.setFormatter(
    Formatter("%(asctime)s@ %(name)s [%(levelname)s] %(funcName)s: %(message)s")
)
# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[stream_handler, file_handler]
)
logger = logging.getLogger(__name__)


"""
Controller
"""
@app.route("/", defaults={"path":""}, methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def index(path):
    ########################################################
    # 受信内容出力
    ########################################################
    logger.info("--- リクエスト受信 ----------------------------")
    try:
        headers = request.headers
        method = request.method
        url = request.url
        query_param = request.args
        data = None
        if (method in ["POST", "PUT"]):
            logger.info("request.is_json: {0}".format(request.is_json))
            if (request.is_json):
                data = request.get_json()
        logger.info("headers: " + str(headers.to_wsgi_list()))
        logger.info("method : {0}".format(method))
        logger.info("url    : {0}".format(url))
        logger.info("path   : {0}".format(path))
        logger.info("query  : " + str(query_param.to_dict()))
        logger.info("data   : {0}".format(data))
    except:
        logger.warning("ログ出力に失敗しました。")

    ########################################################
    # モックレスポンスの取得
    ########################################################    
    # テストを行いながらモックレスポンスを更新することを想定して、このタイミングでモックレスポンス定義ファイルを読み込む
    f = open('./setting/responses.json', 'r', encoding="utf-8")
    mock_response_dict = json.load(f)

    # モックレスポンス定義ファイルから返却できるレスポンスを取得して返却
    for key, value in mock_response_dict.items():
        mock_method = value["method"] or ""
        mock_path = value["path"] or ""
        if (mock_method.lower() == method.lower()) & (is_same_path(path, mock_path)):
            return jsonify(value["response"]["body"]), int(value["response"]["status"])

    # 一致するレスポンスがない場合はデフォルトのレスポンスを返却
    default_mock_response = mock_response_dict["DEFAULT"]
    default_status= default_mock_response["response"]["status"]
    default_content= default_mock_response["response"]["body"]
    logger.warning("Mock Server cannot find response to return.")
    return jsonify(default_content), int(default_status)


if __name__ == "__main__":
    # PORT 取得
    port_file_line = ""
    with open("./setting/port", "r", encoding="utf-8") as f:
        port_file_line = f.readline()
    port = int(port_file_line.replace("/n", "").replace("/r/n", ""))

    # flask起動
    app.run(host="0.0.0.0", port=port)