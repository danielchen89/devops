import requests
import json


def send_msg(msg):
    token = '16a9f365c63bca077649fa06760b73123a9047e678a984926f433cdeec1292ab'
    # token = os.getenv('token')
    url = "https://oapi.dingtalk.com/robot/send?access_token="
    url = url + token
    headers = {'Content-Type': 'application/json'}
    print(url)
    values = """{
      "msgtype":"text",
      "text":{
        "content": "%s"
      }
      }""" % msg

    print(values)
    request = requests.post(url, values, headers=headers)
    return request.text


def lambda_handler(event, context):
    Message = json.loads(event['Records'][0]['Sns']['Message'])
    OldStateValue = Message['OldStateValue']
    NewStateValue = Message['NewStateValue']
    Timestamp = event['Records'][0]['Sns']['Timestamp']
    NewStateReason = json.loads(event['Records'][0]['Sns']['Message'])['NewStateReason']

    msg = "Alarm Details:\n" + "State Change:" + OldStateValue + " -> " + NewStateValue + "\n" \
                                                                                          "Timestamp:" + Timestamp + "\n" \
                                                                                                                     "Reason for State Change:" + NewStateReason

    print(msg)
    send_msg(msg)