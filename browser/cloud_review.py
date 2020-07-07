#!/usr/bin/env python
# -*- coding:utf-8 -*-
__all__ = ('_CloudReview',)

import os
import sys
import platform
from io import BytesIO
import warnings

import re
import json

import time

import requests as req
import mysql.connector
from urllib.parse import unquote

from PIL import Image
import pyzbar.pyzbar as pyzbar

from .block_id import BlockID
from ._browser import SHOTNAME

DB_NAME = 'tieba_imgs'  # 数据库名
system = platform.system()
if system == 'Linux':
    mysql_login = {
        'host':'',
        'user':'',
        'passwd':''
        }  # 链接所需的用户名和密码
else:
    mysql_login = {
        'host':'',
        'user':'',
        'passwd':''
        }

class _CloudReview(BlockID):
    """
    _CloudReview(headers_filepath,ctrl_filepath)

    云审查基类
        参数: raw_headers 字典 包含cookies的原始头
              ctrl_filepath 字符串 控制云审查行为的json的路径
    """

    def __init__(self,headers_filepath,ctrl_filepath):
        self.ctrl_filepath = ctrl_filepath
        review_control = self._link_ctrl_json(ctrl_filepath)
        super(_CloudReview,self).__init__(headers_filepath,review_control['admin_type'])

        try:
            self.tb_name = review_control['tieba_name']
            self.sleep_time = review_control['sleep_time']
            self.cycle_times = review_control['cycle_times']
        except AttributeError:
            self.log.critical('Incorrect format of ctrl json!')
            raise(AttributeError('Incorrect format of ctrl json!'))

        self.table_name=SHOTNAME
        try:
            self.mydb = mysql.connector.connect(host=mysql_login['host'],
                                                user=mysql_login['user'],
                                                passwd=mysql_login['passwd'],
                                                database=DB_NAME)
        except(mysql.connector.errors.ProgrammingError):
            self.mydb = mysql.connector.connect(host=mysql_login['host'],
                                                user=mysql_login['user'],
                                                passwd=mysql_login['passwd'])
            self.mycursor = self.mydb.cursor()
            self.mycursor.execute("CREATE DATABASE {database}".format(database=DB_NAME))
            self.mycursor.execute("USE {database}".format(database=DB_NAME))
            self.mycursor.execute("""
            CREATE PROCEDURE auto_del()
            BEGIN
                DELETE FROM income WHERE DATE(time)<=DATE(DATE_SUB(NOW(),INTERVAL 30 DAY));
            END
            """)
            self.mycursor.execute("""
            CREATE EVENT IF NOT EXISTS event_auto_del
            ON SCHEDULE EVERY 1 DAY STARTS '1980-01-01 00:00:00'
            ON COMPLETION NOT PRESERVE ENABLE DO CALL auto_del();
            """)
        except(mysql.connector.errors.DatabaseError):
            self.log.critical('Cannot link to the database!')
            raise(mysql.connector.errors.DatabaseError('Cannot link to the database!'))
        else:
            self.mycursor = self.mydb.cursor()

        self.mycursor.execute("CREATE TABLE IF NOT EXISTS {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, pid BIGINT)".format(table_name=self.table_name))

    def quit(self):
        self.mydb.commit()
        self.mydb.close()
        super(_CloudReview,self).quit()

    def _mysql_add_pid(self,pid):
        """
        向MySQL中插入pid
        """
        try:
            self.mycursor.execute("INSERT INTO {table_name} VALUES (NULL,{pid})".format(table_name=self.table_name,pid=pid))
        except(mysql.connector.errors.OperationalError):
            self.log.error("MySQL Error: Failed to insert {pid}!".format(pid=pid))
        else:
            self.mydb.commit()

    def _mysql_search_pid(self,pid):
        """
        检索MySQL中是否已有pid
        """
        try:
            self.mycursor.execute("SELECT pid FROM {table_name} WHERE pid={pid}".format(table_name=self.table_name,pid=pid))
        except(mysql.connector.errors.OperationalError):
            self.log.error("MySQL Error: Failed to select {pid}!".format(pid=pid))
            return False
        else:
            return True if self.mycursor.fetchone() else False

    def _scan_QRcode(self,img_url):
        """
        扫描img_url指定的图像中的二维码
        """

        self._set_host(img_url)
        res = req.get(img_url,headers=self.account.headers)
        image = Image.open(BytesIO(res.content))
        raw = pyzbar.decode(image)
        if raw:
            data = unquote(raw[0].data.decode('utf-8'))
            return data
        else:
            return None

    def _link_ctrl_json(self,ctrl_filepath):
        """
        链接到一个控制用的json
        """

        try:
            with open(ctrl_filepath,'r',encoding='utf-8-sig') as review_ctrl_file:
                review_control = json.loads(review_ctrl_file.read())
        except(FileExistsError):
            raise(FileExistsError('review control json not exist! Please create it!'))
        return review_control