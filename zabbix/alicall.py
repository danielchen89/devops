#!/usr/bin/env python
# -*- coding:utf8 -*-

import requests
import json
import sys
import logging

logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.DEBUG, filename='/etc/zabbix/scripts/alicall/calllog.txt', filemode='a')

header = {"Content-Type": "application/json"}
url='http://101.132.113.199:9006/api/alicall/multiAlert'
data = {
            "phoneNumbers": ["xxxxxxxx"]
        }

r = requests.post(url, data=json.dumps(data), headers=header)
print(r.status_code)