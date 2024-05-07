#!/usr/bin/python
# _*_ coding:utf-8 _*_
import cx_Oracle
import socket
import logging
import subprocess
import os

ORACLE_CONFIG = {
    'USER': 'zabbix',
    'PASSWORD': 'Gh7udFJ60J0euh1WoUXx',
    'HOST': '10.1.52.143',
    'PORT': '1543',
    'DATABASE': 'ipay',
}

DATA_FILE = '/etc/zabbix/.data'
ZABBIX_SERVER = 'zabbixserver'
ZABBIX_CMD = 'zabbix_sender'

HOST_IP = 'zabbixserver'
LOG = {
    'filename': '/etc/zabbix/scripts/oracle/trans.log',
    'fmt': "%(asctime)-15s %(levelname)s %(filename)s %(lineno)d %(process)d %(message)s",
    'datefmt': "%a %d %b %Y %H:%M:%S"
}

logger = logging.getLogger('/etc/zabbix/scripts/oracle/trans.log')
logging.basicConfig(filename=LOG['filename'], format=LOG['fmt'], datefmt=LOG['datefmt'])

def get_address():
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        print(host_ip)
        return host_ip
    except Exception as e:
        logger.info(u'获取主机IP失败 {}'.format(e))
        print(u'获取主机IP失败 {}'.format(e))

def get_connection():
    logger.info('===开始连接数据库===')
    #print('===开始连接数据库===')
    dns_tns = cx_Oracle.makedsn(ORACLE_CONFIG['HOST'],
                                ORACLE_CONFIG['PORT'],
                                ORACLE_CONFIG['DATABASE'])
    db = cx_Oracle.connect(ORACLE_CONFIG['USER'],
                           ORACLE_CONFIG['PASSWORD'], dns_tns)
    logger.info('===连接数据库成功===')
    #print('===连接数据库成功===')
    return db.cursor()

def write_data(data):
    with open(DATA_FILE, 'w') as f:
        f.write(data)

def monitor_trad(conn):
    sql = '''
              select  --to_char(sysdate, 'yyyy-mm-dd HH24:MI') time_start,
              x1.success,
              x2.total,
              to_char(trunc(case
                              when x2.total = 0 then
                               0
                              else
                               x1.success / x2.total
                            end,
                            6) * 100)  rate
            from (select count(1) success
                 from ACQUIRE.t_acquire_order
                where OUTER_STATUS = 'success'
                  and GMT_CREATE_TIME >= sysdate - 2 / 1440
                  and GMT_CREATE_TIME < sysdate) x1,
              (select count(1) total
                  from ACQUIRE.t_acquire_order
                 where --OUTER_STATUS='success' and  
                 GMT_CREATE_TIME >= sysdate - 2 / 1440
              and GMT_CREATE_TIME < sysdate) x2
        where 1 = 1'''
    try:
        conn.execute(sql)
        result = conn.fetchall()
    except Exception as e:
        logger.info('执行数据库查询出错 {}'.format(e))
        #print('执行数据库查询出错 {}'.format(e))
    finally:
        conn.close()

    if not result:
        logger.info('获取数据失败')
        #print('获取数据失败')

    if not isinstance(result, list) and len(result != 1):
        logger.info('数据格式不符合')
        #print('数据格式不符合')

    return result

def format_data(host_ip, data):
    try:
        result = '{0}  trad_success {1}\n' \
                 '{0}  trad_total  {2}\n'.format(host_ip, data[0][0], data[0][1])
        logger.info(result)
        return result
    except Exception as e:
        logger.info('格式化数据出错{}'.format(e))
        #print('格式化数据出错{}'.format(e))

def cp_data_to_docker():
    args = "docker cp {0} zabbix-server:{0}".format(DATA_FILE)
    result = os.popen(args).read()
    logger.info(result)

def send_data():
    try:
        # args = [ZABBIX_CMD, '-z', ZABBIX_SERVER, '-i', DATA_FILE]
        # result = subprocess.Popen(args)
        # logger.info(result.stdout)
        args = "{} -z {} -i {}".format(ZABBIX_CMD,ZABBIX_SERVER,DATA_FILE)
        result = os.popen(args).read()
        logger.info(result)
        print(1)
    except Exception as e:
        logger.info('发送数据失败 {}'.format(e))
        print(0)
        #print('发送数据失败 {}'.format(e))

def main():
    logger.info('===开始获取交易量===')
    conn = get_connection()
    data = monitor_trad(conn)
    result = format_data(HOST_IP, data)
    write_data(result)
    send_data()
    logger.info('===获取交易量结束===')

if __name__ == '__main__':
    main()