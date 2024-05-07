#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import requests
import json
import logging
import time
import sys
import copy
logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.DEBUG, filename='/etc/zabbix/scripts/log.txt', filemode='a')


def is_not_null_and_blank_str(content):
    """
    非空字符串
    :param content: 字符串
    :return: 非空 - True，空 - False

    >>> is_not_null_and_blank_str('')
    False
    >>> is_not_null_and_blank_str(' ')
    False
    >>> is_not_null_and_blank_str('  ')
    False
    >>> is_not_null_and_blank_str('123')
    True
    """
    if content and content.strip():
        return True
    else:
        return False


class DingTalk(object):
    """docstring for DingTalk"""

    def __init__(self):

        super(DingTalk, self).__init__()
        self.headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.webhook = 'https://oapi.dingtalk.com/robot/send?access_token=0b28ed6c572ed7f866aadac972e8b41f5e651fff8dda4fbff90c18f4a10e953e'
        self.times = 0
        self.start_time = time.time()

    def is_not_null_and_blank_str(self, content):

        if content and content.strip():
            return True
        else:
            return False

    def post(self, data):

        self.times += 1
        if self.times % 20 == 0:
            if time.time() - self.start_time < 60:
                logging.debug('钉钉官方限制每个机器人每分钟最多发送20条，当前消息发送频率已达到限制条件，休眠一分钟')
                time.sleep(60)
            self.start_time = time.time()

        post_data = json.dumps(data)
        try:
            response = requests.post(self.webhook, headers=self.headers, data=post_data)
            logging.info(post_data)
        except requests.exceptions.HTTPError as exc:
            logging.error("消息发送失败， HTTP error: %d, reason: %s" % (exc.response.status_code, exc.response.reason))
            raise
        except requests.exceptions.ConnectionError:
            logging.error("消息发送失败，HTTP connection error!")
            raise
        except requests.exceptions.Timeout:
            logging.error("消息发送失败，Timeout error!")
            raise
        except requests.exceptions.RequestException:
            logging.error("消息发送失败, Request Exception!")
            raise
        else:
            try:
                result = response.json()
            except JSONDecodeError:
                logging.error("服务器响应异常，状态码：%s，响应内容：%s" % (response.status_code, response.text))
                return {'errcode': 500, 'errmsg': '服务器响应异常'}
            else:
                logging.debug('发送结果：%s' % result)
                if result['errcode']:
                    error_data = {"msgtype": "text", "text": {"content": "钉钉机器人消息发送失，原因：%s" % result['errmsg']}, "at": {"isAtAll": True}}
                    logging.error("消息发送失败，自动通知：%s" % error_data)
                    requests.post(self.webhook, headers=self.headers, data=json.dumps(error_data))
                return result

    def send_text(self, msg, is_at_all=False, at_mobiles=[]):

        data = {"msgtype": "text"}
        if self.is_not_null_and_blank_str(msg):
            data["text"] = {"content": msg}
        else:
            logging.error("text类型，消息内容不能为空！")
            raise ValueError("text类型，消息内容不能为空！")

        if at_mobiles:
            at_mobiles = list(map(str, at_mobiles))

        data["at"] = {"atMobiles": at_mobiles, "isAtAll": is_at_all}
        return self.post(data)

    def send_markdown(self, title, text, is_at_all=False, at_mobiles=[]):

        if self.is_not_null_and_blank_str(title) and self.is_not_null_and_blank_str(text):
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": text
                },
                "at": {
                    "atMobiles": list(map(str, at_mobiles)),
                    "isAtAll": is_at_all
                }
            }
            return self.post(data)
        else:
            logging.error("markdown类型中消息标题或内容不能为空！")
            raise ValueError("markdown类型中消息标题或内容不能为空！")


class Handledata(object):
    """docstring for Handle"""
    @staticmethod
    def json_markdown(data):

        #_data = json.loads(eval(data))
        _data = data.replace('\n','')
        _dict = {
            'from': '告警主机',
            'host': '告警主机',
            'ip': '主机IP',
            'group': '主机组',
            'time': '告警时间',
            'level': '告警级别',
            'name': '告警触发器',
            'key': '告警项目',
            'now': '当前值',
            'status': '当前状态',
            'age': '影响时间',
        }
        _tmp = []
        #_data = copy.deepcopy(_data1)
        #_data['host'] = '[{}][{}]'.format(_data['group'], _data1['from'])


#        for k, v in _data.items():
#            try:
#                #if v == 'PROBLEM':
#                #    c_status = '#FF0000'
#                #    _v = '<font color="#000000">{}</font>: <font color="{}">{}</font><br>'.format(_dict[k], c_status, v)
#                #elif v == 'RESOLVED':
#		#    c_status = '#008000'
#                #    _v = '<font color="#000000">{}</font>: <font color="{}">{}</font><br>'.format(_dict[k], c_status, v)
#
#                #_v = '<font color="#000000">{}</font>: {}\n'.format(_dict[k], v)
#
#                _v = '{}: {}\n'.format(_dict[k],v.encode('UTF-8'))
#                _tmp.append(_v)
#            except KeyError:
#                pass
        #return {'title': _data['name'], 'msg': '> '+('').join(_tmp)}
#	return {'msg': ('').join(_tmp)}
        return {'msg':_data}
if __name__ == '__main__':

    ins = DingTalk()
    logging.info(sys.argv[1])
    res = Handledata.json_markdown(sys.argv[1])
    ins.send_text(res['msg'])
