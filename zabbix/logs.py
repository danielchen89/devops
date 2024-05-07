# -*- coding: utf-8 -*-

import os
import sys
import collections
import json
import commands


class Logs_Discovery(object):

    def __init__(self):
        super(Logs_Discovery, self).__init__()
        self.data = collections.defaultdict(list)

    def get_logs_list(self):

        t1, s1 = commands.getstatusoutput('ls  /data/logs')
        t2, s2 = commands.getstatusoutput('cd /data/ && ls -d tomcat-*')

        logs_dir = s1.split('\n') + s2.split('\n')

        for l in logs_dir:
            if 'tomcat' in l:
                _dict = {'{#LOGSERVICE}': l, '{#FILES}': '/data/{0}/logs/.*out'.format(l)}
            else:
                _dict = {'{#LOGSERVICE}': l, '{#FILES}': '/data/logs/{0}/.*log'.format(l)}
            self.data['data'].append(_dict)
        return json.dumps(self.data)

if __name__ == '__main__':

    ins = Logs_Discovery()
    if sys.argv[1] == 'list':
        print ins.get_logs_list()

