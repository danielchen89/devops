import json



data={'Records': [{'EventSource': 'aws:sns', 'EventVersion': '1.0', 'EventSubscriptionArn': 'arn:aws:sns:us-west-1:757920318787:sns-test:ce7262c0-8c9b-4111-be1a-3250f5c11630', 'Sns': {'Type': 'Notification', 'MessageId': 'f400a0df-9f84-5895-af77-f84931975fa1', 'TopicArn': 'arn:aws:sns:us-west-1:757920318787:sns-test', 'Subject': 'ALARM: "CPU-test" in US West (N. California)', 'Message': '{"AlarmName":"CPU-test","AlarmDescription":null,"AWSAccountId":"757920318787","NewStateValue":"ALARM","NewStateReason":"Threshold Crossed: 1 out of the last 1 datapoints [3.22916666666667 (05/02/21 02:20:00)] was greater than the threshold (2.0) (minimum 1 datapoint for OK -> ALARM transition).","StateChangeTime":"2021-02-05T02:22:11.231+0000","Region":"US West (N. California)","AlarmArn":"arn:aws:cloudwatch:us-west-1:757920318787:alarm:CPU-test","OldStateValue":"INSUFFICIENT_DATA","Trigger":{"MetricName":"CPUUtilization","Namespace":"AWS/ElastiCache","StatisticType":"Statistic","Statistic":"AVERAGE","Unit":null,"Dimensions":[{"value":"risk-ip-finger-prod-002","name":"CacheClusterId"},{"value":"0001","name":"CacheNodeId"}],"Period":60,"EvaluationPeriods":1,"ComparisonOperator":"GreaterThanThreshold","Threshold":2.0,"TreatMissingData":"- TreatMissingData: missing","EvaluateLowSampleCountPercentile":""}}', 'Timestamp': '2021-02-05T02:22:11.274Z', 'SignatureVersion': '1', 'Signature': 'wPS3TYatObPey98mn/H0CUjdhI2LWWQEmmrz6YUvSegWHRGyZXjYvhm9wFl4drytTmz4WiI9p8BRmkBo647esp7gmWVmPzNtN93HhRBii743OZyY+ovcKfR6usJcbYjum70tMcw2g1dtdQuoRtIlk0hIAeBCQ7g/z00DHXu1MbThyyg3kE6gT5r1F1egD/4vXOdXbgzUxR/r1OEcqVOWlc2wyqDViasE6eDP5Ix2xFPXYS6GAWOtdlK9MNlEgF1/CM6llQABAeoBriyHZdyBlbMlD8PAPFkJbfR6DN8hs50tqeIinvfeguzNo4Hr3D9mmuNM8lFfschobyFUFp7Ceg==', 'SigningCertUrl': 'https://sns.us-west-1.amazonaws.com/SimpleNotificationService-010a507c1833636cd94bdb98bd93083a.pem', 'UnsubscribeUrl': 'https://sns.us-west-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-1:757920318787:sns-test:ce7262c0-8c9b-4111-be1a-3250f5c11630', 'MessageAttributes': {}}}]}

event_str = json.dumps(data, sort_keys=True)
# 将 JSON 对象转换为 Python 字典
event = json.loads(event_str)

print(event)
print("------------------------------------")
message = event['Records'][0]['Sns']
subject = message['Subject']
item = subject.split(':')[1].replace('"', '')
# print(item)
# print("------------------------------------")
description = json.loads(event['Records'][0]['Sns']['Message'])['NewStateReason']
print(description)
print("---------------------------------")
current_value=round(float(description.split('[')[1].split(' ')[0]),2)
print(current_value)
# node=json.loads(event['Records'][0]['Sns']['Message'])['Trigger']['Dimensions'][0]['value']
# print(node)

