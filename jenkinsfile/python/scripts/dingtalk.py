# -*- coding: utf-8 -*-
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests,json   #导入依赖库

timestamp = str(round(time.time() * 1000))
# secret = 'SEC6970c5a4763d3bb5c32a3648844c7816e83b943766eae0b54119d5d15de4dd02'
secret = 'SEC56a6fde5760ddd51fc13f000ddc7495a97b599f3ae21eb8f4c5538b5c6558f38'
secret_enc = secret.encode('utf-8')
string_to_sign = '{}\n{}'.format(timestamp, secret)
string_to_sign_enc = string_to_sign.encode('utf-8')
hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

import subprocess
JOB_NAME_sh = "echo $JOB_NAME"
BUILD_URL_sh = "echo $BUILD_URL"

(JOB_NAME_STATUS,JOB_NAME) = subprocess.getstatusoutput(JOB_NAME_sh)
(JOB_URL_STATUS,BUILD_URL) = subprocess.getstatusoutput(BUILD_URL_sh)
BUILD_URL = BUILD_URL + 'console'

def dingTalkAlert(branch):
    headers={'Content-Type': 'application/json'}   #定义数据类型
    webhook = 'https://oapi.dingtalk.com/robot/send?access_token=c74578cc5fafd929e366a388402a385274bac78c08872812d30794b4efbabc19&timestamp='+timestamp+"&sign="+sign
    # webhook = 'https://oapi.dingtalk.com/robot/send?access_token=dc196c3d547c07c556e9b47bb181a363aa1a13a80bd7b46386955b9ed98c1091&timestamp='+timestamp+"&sign="+sign
    #"at": {"atMobiles": "['"+ mobile + "']"
    content = '应用 ' + JOB_NAME + ' 本次构建失败!!! \n' \
            '构建分支: ' + branch + '\n' \
            '构建地址: ' + BUILD_URL
    data = {
        "msgtype": "text",
        "text": {"content": content },
        "isAtAll": True}
    res = requests.post(webhook, data=json.dumps(data), headers=headers)   #发送post请求

    # print(res.text)


