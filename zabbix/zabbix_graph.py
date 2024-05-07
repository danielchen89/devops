# -*- coding: UTF-8 -*-
import urllib.request,json,cookielib,urllib,datetime,os,threading
from urllib.request import Request, urlopen, URLError, HTTPError
global auth_code,zabbix_url,zabbix_header,login_url,graph_url,login_data,pic_save_path_dir,yesterday9,opener
#zabbix接口地址、登录地址、图片地址
zabbix_url="http://172.168.1.243:8000/api_jsonrpc.php"
login_url = 'http://172.168.1.243:8000/index.php'
graph_url = 'http://172.168.1.243:8000/chart2.php'

zabbix_header = {"Content-Type":"application/json"}
zabbix_user   = "Admin"
zabbix_pass   = "zabbix"
auth_code     = ""
auth_data = json.dumps({
    "jsonrpc":"2.0",
    "method":"user.login",
    "params":
            {
            "user":zabbix_user,
            "password":zabbix_pass
            },
    "id":0
    })

#定义登录所需要用的信息，如用户名、密码等，使用urllib进行编码
login_data = urllib.urlencode({
                        "name": zabbix_user,
                        "password": zabbix_pass,
                        "autologin": 1,
                        "enter": "Sign in"})

#新建以当天日期为名的文件夹保存图片
today = datetime.datetime.now().date().strftime('%Y%m%d')
pic_save_path_dir= os.path.join('/tmp',today ) #修改图片保存位置
if not os.path.exists(pic_save_path_dir):
    os.makedirs(pic_save_path_dir)

#定义graph的starttime参数，从前一天的9:00开始
yesterday = (datetime.datetime.now()-datetime.timedelta(days=1))
yesterday9 = datetime.datetime(yesterday.year,yesterday.month,yesterday.day,9).strftime('%Y%m%d%H%M%S')

#登录zabbix，设置一个cookie处理器，负责从服务器下载cookie到本地，并且在发送请求时带上本地的cookie  
cj = cookielib.CookieJar() 
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)) 
urllib.request.install_opener(opener) 
opener.open(login_url,login_data)#.read()

request = urllib.request.Request(zabbix_url,auth_data)
for key in zabbix_header:
    request.add_header(key,zabbix_header[key])
try:
    result = urllib.request.urlopen(request)
except HTTPError as e:
    print('The server couldn\'t fulfill the request, Error code: ', e.code)
except URLError as e:
    print('We failed to reach a server.Reason: ', e.reason)
else:
    response=json.loads(result.read())
    #print response
    result.close()

#判断SESSIONID是否在返回的数据中
if  'result'  in  response:
    auth_code=response['result']
else:
    print(response['error']['data'])

def Http_access(data):
    request = urllib.request.Request(zabbix_url,data)
    for key in zabbix_header:
        request.add_header(key,zabbix_header[key])
    result = urllib.request.urlopen(request)
    
    response = json.loads(result.read())
    # print result.read()
    # print response
    result.close()  
    if len(response['result']) > 0:
        return response['result'][0]

def get_hostid(ip):
    get_host_data = ''
    if len(auth_code) != 0:
        get_host_data = json.dumps({
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": "extend",
                "filter": {
                    "host": [
                        ip,
                    ]
                }
            },
            "auth": auth_code,
            "id": 1
        })
    return get_host_data 

def get_itemid(hostid,itemtype):
    get_item_data = ''
    if (len(auth_code) != 0) and (hostid is not None):
        get_item_data = json.dumps({
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": "extend",
                "hostids": hostid,
                "search":{
                "name": itemtype
                        },
            "sortfield": "name"
                    },
            "auth": auth_code,
            "id": 1
        })
    return get_item_data


def get_graphid(itemid):
    get_graph_data = ''
    if (len(auth_code) != 0) and (itemid is not None):
        get_graph_data = json.dumps({
            "jsonrpc": "2.0",
            "method": "graphitem.get",
            "params": {
                "output": "extend",
                "expandData": 1,
                "itemids": itemid
            },
            "auth": auth_code,
            "id": 1
        })
    return get_graph_data

def pic_save(ip,name,graphid):
    graph_args = urllib.urlencode({
                            "graphid":graphid,
                            "width":'400', #定义图片宽度
                            "height":'156', #定义图片高度
                            "stime":yesterday9, #图形开始时间
                            "period":'86400'}) #定义时长，取1天的数据

    data = opener.open(graph_url,graph_args).read()
    #pic_save_path = pic_save_path_dir + ip + '-' + name +'.png'
    picname = ip + '-' + name +'.png'
    pic_save_path = os.path.join(pic_save_path_dir,picname)
    file=open(pic_save_path,'wb')
    file.write(data)
    #file.flush()
    file.close()

#多线程并发调用该函数
def pic_save_th(ip):
    #根据ip获取hostid
    host_data = get_hostid(ip)
    host_result = Http_access(host_data)
    if host_result is not None: #判断该IP是否在zabbix中存在
        hostid = host_result['hostid'] 

        #根据监视器名称获取相应的itemid
        cpuname = 'CPU Usage'
        memoryname = 'Memory - Memory available'
        diskname = 'Disk - Current Disk Queue Length'
        netcard = 'Traffic for Public Receive'
        item_cpu = get_itemid(hostid,cpuname)
        item_memory = get_itemid(hostid,memoryname)
        item_disk = get_itemid(hostid,diskname)
        item_netcard = get_itemid(hostid,netcard)

        itemid_cpu = Http_access(item_cpu)['itemid'] 
        itemid_memory = Http_access(item_memory)['itemid'] 
        itemid_disk = Http_access(item_disk)['itemid'] 
        itemid_netcard = Http_access(item_netcard)['itemid'] 

        #根据itemid获取相应的graphid
        graphdata_cpu = get_graphid(itemid_cpu)
        graphdata_memory = get_graphid(itemid_memory)
        graphdata_disk = get_graphid(itemid_disk)
        graphdata_netcard = get_graphid(itemid_netcard)

        graphid_cpu = Http_access(graphdata_cpu)['graphid'] 
        graphid_memory = Http_access(graphdata_memory)['graphid'] 
        graphid_disk = Http_access(graphdata_disk)['graphid'] 
        graphid_netcard = Http_access(graphdata_netcard)['graphid'] 

        print(ip)#,graphid_cpu,graphid_memory,graphid_disk,graphid_netcard

        #调用pic_save函数保存图片到本地
        pic_save(ip,cpuname,graphid_cpu)
        pic_save(ip,memoryname,graphid_memory)
        pic_save(ip,diskname,graphid_disk)
        pic_save(ip,netcard,graphid_netcard)
    else:
        print('%s doesnot exist in zabbix' % ip)

#定义线程数控制函数，num表示每次并发的线程数
def lstg(num,lst):
#定义每段的个数num
    l = len(lst)
    g = l/num #取分成几组
    last = l%num #判断是否有剩余的数
    lstn = []
    if num >= l:
        lstn.append(lst)
    else:
        for i in range(g):
            i=i+1
            n=i*num
            m=n-num 
            lstn.append(lst[m:n])

        if  last != 0:
            lstn.append(lst[-last:])
    return lstn

    
if __name__ =='__main__':
    #定义线程数量
    tnum = 5
    serverips=['172.168.1.243','172.168.1.248']
    for ips in lstg(tnum,serverips):
        threads=[]
        for ip in ips:
            #创建并启动进程
            t = threading.Thread(target=pic_save_th,args=(ip,))
            #t.setName('th-'+ ip)
            t.setDaemon(True)
            t.start()
            threads.append(t)
        #等待每个线程结束   
        for t in threads:
            #print t.name,t.is_alive(),ctime()
            t.join()