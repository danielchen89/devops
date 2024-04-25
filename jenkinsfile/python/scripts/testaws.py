#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import json

def get_token():
    url = 'https://ops.corp.ipaylinks.com/api/users/v1/token/'

    query_args = {
        "username": "jenkins",
        "password": "*cailing*0118abc"
    }
    response = requests.post(url, data=query_args)
    return json.loads(response.text)['Token']


def post_build_aws(data):
    url = 'https://ops.corp.ipaylinks.com/api/publish/v1/build/tasks/'

    token = get_token()
    print(token)
    header_info = {"Authorization": 'Bearer ' + token}

    query_args = {
        "version": "version",
        "project": "project",
        "url": "url",
        "md5": "md5",
        "data": data,
    }

    response = requests.post(url, data=query_args, headers=header_info)
    return json.loads(response.text)

data = {"finished_timestamps": 1602769752855, "project": "mpsnew", "version": "20201015214912856_dev_v2.7.5_20200910", "branch": "dev_v2.7.5_20200910", "url": "/data/package/2020-10-15/20201015214912856_dev_v2.7.5_20200910/mpsnew.tar.gz", "md5": "bdd6a07f02316dcf0c5ec2a51e12bd0b"}
jsondata = json.dumps(data)
print(post_build_aws(jsondata))
# get_token()
