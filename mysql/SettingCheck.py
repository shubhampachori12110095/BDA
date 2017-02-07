#!/usr/bin/python
# -*- coding:utf-8 -*-
import xml.etree.ElementTree as ET
import MySQLdb, os
import MySQLdb.cursors
from Logger import Log

class ConfScan(object):
    def __init__(self, username,password, host='127.0.0.1', port=3306):
        self.__username = username
        self.__password = password
        self.__host = host
        self.__port = port
        self.conn = None
        self.cursor = None

    """
    连接数据库
    """
    def connect(self):
        try:
            self.conn = MySQLdb.connect(host=self.__host, user=self.__username, passwd=self.__password,
                                   port=self.__port, cursorclass = MySQLdb.cursors.DictCursor)
            self.cursor = self.conn.cursor()
            # res = cur.execute('select * from user');
            # info = cur.fetchmany(res)
            # for data in info:
            #     print data
            # cur.close()
            # conn.close()
        except MySQLdb.Error, e:
            Log.log_error('MySql Error %%s'% str(e))

    """
    判断是否存在无用的数据库
    """
    def hasUselessDb(self, dbs=list):
        if self.cursor is None:
            self.connect()
        self.cursor.execute("show databases")
        for data in self.cursor.fetchall():
            if data['Database'] in dbs:
                Log.log_warn("have useless db %s "% data['Database'])

    """
    判断是否含有废弃或者匿名账户
    """
    def hasObsoleteAccount(self, username=""):
        if self.conn is None:
            self.connect()
        res = self.cursor.execute("select * from mysql.user where user='%s'"%username)
        if res > 0:
            Log.log_warn("has obsolete account!")
        else:
            Log.log_pass("has no obsolete account")

    """"
    判断是否可以加载本地文件
    """
    def loadInfile(self):
        if self.conn is None:
            self.connect()
        res = self.cursor.execute("select load_file('/etc/passwd')")
        # print res

    """
    判断是否启用日志
    """
    def logStatus(self, conf=dict):
        if self.conn is None:
            self.connect()
        self.cursor.execute("show variables like '%log%'")
        res = self.cursor.fetchall()
        for data in res:
            key = data['Variable_name']
            val = data['Value']
            if key in conf.keys():
                if val != conf[key]:
                    Log.log_warn('set %s = %s is not safe!'%(key, val))

    """
    检查用户的全局权限
    """
    def checkUserGlGrants(self, username):
        if self.cursor is None:
            self.connect()
        self.cursor.execute("select Grant_priv, References_priv,Alter_routine_priv,Create_routine_priv,File_priv,"
                            "Create_tmp_table_priv, Lock_tables_priv, Execute_priv,Create_user_priv,Process_priv,"
                            "Reload_priv,Repl_slave_priv, Repl_client_priv, Show_db_priv,Shutdown_priv,Super_priv from mysql.user "
                            "where User ='%s'"%username)
        res = self.cursor.fetchall()
        flag = 0
        for row in res:
            # print row
            for key,value in row.items():
                if value == 'Y':
                    flag = 1
                    Log.log_warn('setting %s = %s is suggested!' %(key,'N'))
        if (flag == 0):
            Log.log_pass('All the setting are approriate!')

    """
    检查用户对应的数据库权限
    """
    def checkUserDbGrants(self, username):
        if self.cursor is None:
            self.connect()
        self.cursor.execute("select Drop_priv, Grant_priv, References_priv,Create_tmp_table_priv,"
                            "Lock_tables_priv,Create_routine_priv,Alter_routine_priv,Execute_priv,"
                            "Event_priv,Trigger_priv from mysql.db "
                            "where User ='%s'" % username)
        res = self.cursor.fetchall()
        flag = 0
        for row in res:
            # print row
            for key, value in row.items():
                if value == 'Y':
                    flag = 1
                    LOg.log_warn('setting %s = %s is suggested!' % (key, 'N'))
        if (flag == 0):
            Log.log_pass('All the setting are approriate!')

    """
    关闭数据库
    """
    def close(self):
        if self.cursor is not None:
            self.cursor.close()
        if self.conn is not None:
            self.conn.close()


def run(settingFilePath):
    if not os.path.isfile(settingFilePath):
        Log.log_error ('%s doesn`t exists!' % config_file_path)
        sys.exit(0)

    root = ET.parse(settingFilePath).getroot()
    username = root.find('.//user/username').text
    password = root.find(".//user/password").text
    
    test = ConfScan(username, password)
    test.connect()

    Log.log_info("检查是否存在无用的数据库...")
    test.hasUselessDb(dbs={'test', 'mysql', 'information_schema'})

    Log.log_info("检查是否存在废弃或者匿名账号...")
    test.hasObsoleteAccount("")

    Log.log_info("检查是否能从客户端加载数据库服务器本地文件...")
    test.loadInfile()

    Log.log_info("检查log的配置文件是否安全...") 
    log_conf = dict()
    log_conf_dom = root.find(".//conf/log")
    for item in log_conf_dom:
        key = item.find('./key').text
        val = item.find('./val').text
        log_conf[key] = val
        # print key,val
    # print log_conf
    test.logStatus(log_conf)

    Log.log_info('检测指定用户的全局权限是否合理')
    test.checkUserGlGrants('test')

    Log.log_info('检测指定用户的对应数据库权限是否合理')
    test.checkUserDbGrants('test')


if __name__ == '__main__':
    run("conf.xml")
    




