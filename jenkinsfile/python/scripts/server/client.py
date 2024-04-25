import requests
import json
url = 'http://10.0.100.208:5678/push'

data = {
    'image':'registry.cn-shanghai.aliyuncs.com/ipay/unified-filesystem:20210507165809340_dev_cly'
}
requests.post(url=url,data=json.dumps(data))
