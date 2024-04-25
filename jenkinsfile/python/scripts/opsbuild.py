#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import json

def get_token():
    url = 'https://ops.ipaylinks.com/api/users/v1/token/'

    query_args = {
        "username": "jenkins",
        "password": "*cailing*0118abc"
    }
    response = requests.post(url, data=query_args)
    return json.loads(response.text)['Token']

def post_build(data):
    url = 'https://ops.ipaylinks.com/api/publish/v1/build/tasks/'

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

token=get_token()
print(token)
