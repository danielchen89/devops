import json
import urllib3
import boto3
import datetime
import time

def lambda_handler(event, context):
    url = 'https://oapi.dingtalk.com/robot/send?access_token=0b28ed6c572ed7f866aadac972e8b41f5e651fff8dda4fbff90c18f4a10e953e'
    message = event['Records'][0]['Sns']
    _timestamp = datetime.datetime.strptime(message['Timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=8)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.mktime(_timestamp.timetuple()))))
    subject = message['Subject']
    item = subject.split(':')[1].replace('"', '')
    node = node=json.loads(event['Records'][0]['Sns']['Message'])['Trigger']['Dimensions'][0]['value']
    description = json.loads(event['Records'][0]['Sns']['Message'])['NewStateReason']
    current_value = round(float(description.split('[')[1].split(' ')[0]), 2)
    service_name = 'redis'
    if 'ALARM' in subject:
        title = '告警状态： PROBLEM'
        text = "{}  \n\n 告警服务: {} \n\n 告警节点: {} \n\n 告警项目: {}\n\n 当前值：{} \n\n 告警时间: {}\n\n ".format(title,service_name, node, item,current_value,
                                                                                                     timestamp)
    elif 'OK' in subject:
        title = '告警状态： RESOLVED'
        text = "{} \n\n 告警服务: {} \n\n  告警节点: {} \n\n 告警项目: {}\n\n 当前值：{} \n\n 告警时间: {}\n\n".format(title, service_name,node, item,
                                                                                                     current_value,
                                                                                                     timestamp)
    param = {
        "msgtype": "markdown",
        "markdown": {"title": title,
                     "text": text
                     },
        "isAtAll": "true"
    }
    headers = {
        'Content-Type': 'application/json'
    }

    http = urllib3.PoolManager()
    response = http.request('POST',
                            url,
                            body=json.dumps(param),
                            headers={'Content-Type': 'application/json'},
                            retries=False)