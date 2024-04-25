# -*- coding: utf-8 -*
import os
import oss2
import sys

# localdir="mpsnew.tar.gz"
# remotepath="publish/mpsnew/20201016154124672_dev_v2.7.5_20200910/mpsnew.tar.gz"

def upload_oss(localdir, remotepath):
    try:
        global access_key_id, access_key_secret
        access_key_id = 'xxxxxxxxxxxxxxx'
        access_key_secret = 'xxxxxxxxxxxxx'
        bucket_name = "xxxxxxxxxxxxxx"
        endpoint = "oss-cn-shanghai-internal.aliyuncs.com"

        for param in (access_key_id, access_key_secret, bucket_name, endpoint):
            assert '<' not in param, '请设置参数：' + param

        bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)
        filename = localdir
        key = remotepath

        total_size = os.path.getsize(filename)
        part_size = oss2.determine_part_size(total_size, preferred_size=1024 * 1024)
        upload_id = bucket.init_multipart_upload(key).upload_id
        with open(filename, 'rb') as fileobj:
            parts = []
            part_number = 1
            offset = 0
            while offset < total_size:
                num_to_upload = min(part_size, total_size - offset)
                result = bucket.upload_part(key, upload_id, part_number,
                                            oss2.SizedFileAdapter(fileobj, num_to_upload))
                parts.append(oss2.models.PartInfo(part_number, result.etag))

                offset += num_to_upload
                part_number += 1
            # 完成分片上传
            bucket.complete_multipart_upload(key, upload_id, parts)
    except Exception as err:
        print("上传错误" + err)

    return True
# print(upload_oss(localdir, remotepath))








