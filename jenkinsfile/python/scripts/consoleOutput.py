# -*- coding:utf-8 -*-
import os
import sys
import json
from opsbuildaws import post_build_aws
from uploadOss import upload_oss

gitlabSourceRepoSshUrl=sys.argv[1]
project = gitlabSourceRepoSshUrl.split(":")[1].split(".")[0].strip()
service=project.split("/")[1]
branch = sys.argv[2]
json_file="/tmp/{}_{}.json".format(service,branch)

def console_output_uploadoss(json_file):
    with open(json_file) as fp:
        json_dict = json.load(fp)
        finished_timestamps = json_dict['finished_timestamps']
        application_name = json_dict['project']
        version = json_dict['version']
        branch = json_dict['branch']
        path = json_dict['url']
        md5 = json_dict['md5']

    # path=None的时候是基础包
    if path is not None:
        data = {"finished_timestamps": finished_timestamps, "project": application_name, \
                "version": version, "branch": branch, "url": path, "md5": md5}

        jsondata = json.dumps(data)

        remotepath = "publish/" + application_name + "/" + path.split("/")[-2] + "/" + path.split("/")[-1]
        upload_status = upload_oss(path, remotepath)
        if upload_status:
            post_build_aws(jsondata)
            print("steps: Upload package to oss successfully...")
        else:
            print("steps: Upload package to oss failed...")
            sys.exit(1)
        print("""
              -------------this build's package infomation-------------
              finished timestamps:{}
              application name: {} 
              version: {}
              branch: {}
              package path: {}
              md5: {}
              ---------------------------------------------------------

              """.format(finished_timestamps, application_name, version, branch, path, md5))
    else:
      print("package is base service, no need to upload package to oss")

if os.path.exists(json_file):
    console_output_uploadoss(json_file)
else:
    print("these is not tmp json file")
    # sys.exit(1)
