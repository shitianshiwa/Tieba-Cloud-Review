#!/usr/bin/env python
# -*- coding:utf-8 -*-
__all__ = ('_Browser','SCRIPT_PATH','FILENAME','SHOTNAME')

import os
import sys
import time
import logging
from functools import wraps

import hashlib

import requests as req

import re
import json
import html
import pickle
from bs4 import BeautifulSoup


PATH = os.path.split(os.path.realpath(__file__))[0].replace('\\','/')
SCRIPT_PATH,FILENAME = os.path.split(os.path.realpath(sys.argv[0]))
SCRIPT_PATH = SCRIPT_PATH.replace('\\','/')
SHOTNAME = os.path.splitext(FILENAME)[0]


class _Thread():
    """
    主题帖信息

    tid:帖子编号
    pid:回复编号
    topic:标题
    user_name:发帖用户名
    nick_name:发帖人昵称
    portrait:用户头像portrait值
    reply_num:回复数
    """

    __slots__ = ('tid','pid','topic','user_name','nick_name','portrait','reply_num')

    def __init__(self):
        pass


class _Post():
    """
    楼层信息

    text:正文
    tid:帖子编号
    pid:回复编号
    user_name:发帖用户名
    nick_name:发帖人昵称
    portrait:用户头像portrait值
    level:用户等级
    floor:楼层数
    comment_num:楼中楼回复数
    sign:签名照片
    imgs:图片列表
    smileys:表情列表
    """

    __slots__ = ('text','tid','pid','user_name','nick_name','portrait','level','floor','comment_num','sign','imgs','smileys')

    def __init__(self):
        pass


class _Comment():
    """
    楼中楼信息

    text:正文
    tid:帖子编号
    pid:回复编号
    user_name:发帖用户名
    nick_name:发帖人昵称
    portrait:用户头像portrait值
    smileys:表情列表
    """

    __slots__ = ('text','tid','pid','user_name','nick_name','portrait','smileys')

    def __init__(self):
        pass


class _Headers():
    """
    消息头
    """

    __slots__ = ('headers','cookies')

    def __init__(self,filepath):
        self.update(filepath)

    def update(self,filepath:str):
        """
        Read headers.txt and return the dict of headers.
        read_headers_file(filepath)

        Parameters:
            filepath:str Path of the headers.txt
        """
        self.headers = {}
        self.cookies = {}
        try:
            with open(filepath,'r',encoding='utf-8') as header_file:
                rd_lines = header_file.readlines()
                for text in rd_lines:
                    text = text.replace('\n','').split(':',1)
                    self.headers[text[0].strip()] = text[1].strip()
        except(FileExistsError):
            raise(FileExistsError('headers.txt not exist! Please create it from browser!'))

        if self.headers.__contains__('Referer'):
            del self.headers['Referer']
        if self.headers.__contains__('Cookie'):
            for text in self.headers['Cookie'].split(';'):
                text = text.strip().split('=')
                self.cookies[text[0]] = text[1]
        else:
            raise(AttributeError('raw_headers["cookies"] not found!'))


class _Browser():
    """
    贴吧部分浏览&删帖API的封装
    _Browser(headers_filepath:str)
    """

    old_del_api = 'http://tieba.baidu.com/bawu2/postaudit/audit'
    new_del_post_api = 'http://tieba.baidu.com/f/commit/post/delete'
    new_del_thread_api = 'https://tieba.baidu.com/f/commit/thread/delete'
    new_del_batch_api = 'https://tieba.baidu.com/f/commit/thread/batchDelete'
    new_block_api = 'http://tieba.baidu.com/pmc/blockid'
    old_block_api = 'http://c.tieba.baidu.com/c/c/bawu/commitprison'
    tbs_api = 'http://tieba.baidu.com/dc/common/tbs'
    fid_api = 'http://tieba.baidu.com/sign/info'
    portrait_api = 'http://tieba.baidu.com/i/sys/user_json'

    tieba_url = 'http://tieba.baidu.com/f'
    tieba_post_url = 'http://tieba.baidu.com/p/'
    user_homepage_url = 'https://tieba.baidu.com/home/main/'
    comment_url = 'http://tieba.baidu.com/p/comment'

    def __init__(self,headers_filepath:str):
        """
        _Browser(headers_filepath:str)
        """

        if not os.path.exists(PATH + '/log'):
            os.mkdir(PATH + '/log')
        recent_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))

        log_filepath = ''.join([PATH,'/log/',SHOTNAME.upper(),'_',recent_time,'.log'])
        try:
            file_handler = logging.FileHandler(log_filepath,encoding='utf-8')
        except(PermissionError):
            try:
                os.remove(log_filepath)
            except(OSError):
                raise(OSError('''Can't write and remove {path}'''.format(path=log_filepath)))
            else:
                file_handler = logging.FileHandler(log_filepath,encoding='utf-8')

        formatter = logging.Formatter("<%(asctime)s> [%(levelname)s]  %(message)s","%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        self.log = logging.getLogger(__name__)
        self.log.addHandler(file_handler)
        self.log.setLevel(logging.INFO)

        self.fid_cache_filepath = PATH + '/cache/fid_cache.pk'
        try:
            with open(self.fid_cache_filepath,'rb') as pickle_file:
                self.fid_dict = pickle.load(pickle_file)
        except(FileNotFoundError,EOFError):
            self.log.warning('"{filepath}" not found. Create new fid_dict'.format(filepath=self.fid_cache_filepath))
            self.fid_dict = {}

        self.account = _Headers(headers_filepath)

    def quit(self):
        """
        自动缓存fid信息
        """
        try:
            with open(self.fid_cache_filepath,'wb') as pickle_file:
                pickle.dump(self.fid_dict,pickle_file)
        except AttributeError:
            self.log.warning("Failed to save fid cache!")

    def _set_host(self,url:str):
        try:
            self.account.headers['Host'] = re.search('://(.+?)/',url).group(1)
        except AttributeError:
            self.log.warning('Wrong type of url "{url}"!'.format(url=url))

    def _get_tbs(self):
        self._set_host(self.tbs_api)
        res = req.get(self.tbs_api, headers = self.account.headers).text
        tbs = re.search('"tbs":"([a-z\d]+)',res).group(1)
        return tbs

    def _get_fid(self,tb_name:str):
        if self.fid_dict.__contains__(tb_name):
            return self.fid_dict[tb_name]
        else:
            self._set_host(self.fid_api)
            raw = None
            count = 0
            while not raw and count < 4:
                res = req.get(self.fid_api,params={'kw':tb_name,'ie':'utf-8'}, headers = self.account.headers).text
                raw = re.search('"forum_id":(\d+)', res)
                count+=1
            if raw:
                fid = raw.group(1)
                self.fid_dict[tb_name] = fid
                return fid
            else:
                self.log.critical("Failed to get fid of {name}".format(name=tb_name))
                raise(ValueError("Failed to get fid of {name}".format(name=tb_name)))

    def _get_sign(self,data):
        raw_list = []
        for key,value in data.items():
            raw_list.extend([key,'=',str(value)])
        raw_str = ''.join(raw_list) + 'tiebaclient!!!'
        md5 = hashlib.md5()
        md5.update(raw_str.encode('utf-8'))
        sign = md5.hexdigest().upper()
        return sign

    def _get_portrait(self,name):
        self._set_host(self.user_homepage_url)
        res = req.get(self.user_homepage_url,params={'un':name},headers=self.account.headers).text
        portrait = re.search('data-sign="([\w\.-]+)',res).group(1)
        return portrait

    def _get_threads(self,tb_name,pn=0):
        """
        获取首页帖子
        _get_threads(tb_name,pn=0)

        Returns:
            _Thread
        """

        try:
            threads = []
            self._set_host(self.tieba_url)
            res = html.unescape(req.get(self.tieba_url,params={'kw':tb_name,'pn':pn,'ie':'utf-8'}, headers=self.account.headers).text)
            raws = re.findall('thread_list clearfix([\s\S]*?)创建时间"',res)
            for raw in raws:
                thread = _Thread()
                thread.tid = re.search('href="/p/(\d*)', raw).group(1)
                thread.pid = re.search('"first_post_id":(.*?),', raw).group(1)
                thread.topic = html.unescape(re.search('href="/p/.*?" title="([\s\S]*?)"', raw).group(1))
                thread.reply_num = re.search('"reply_num":(.*?),',raw).group(1)
                thread.user_name = re.search('''frs-author-name-wrap"><a rel="noreferrer"  data-field='{"un":"(.*?)",''',raw).group(1).encode('utf-8').decode('unicode_escape')
                thread.nick_name = re.search('title="主题作者: (.*?)"', raw).group(1)
                thread.portrait = re.search('id":"(.*?)"}',raw).group(1)
                threads.append(thread)
            if threads == []:
                raise(ValueError("Failed to get threads!"))
        except(ValueError,IndexError):
            self.log.error("Failed to get threads!")
        finally:
            return threads

    def _get_posts(self,tid,pn=0):
        """
        获取帖子回复
        _get_post(tid,pn=0)

        Returns:
            _Post
        """

        tid = str(tid)
        self._set_host(self.tieba_post_url)

        post_list = []
        raw = None
        retry_times = 3
        while not raw and retry_times:
            try:
                raw = req.get(self.tieba_post_url + tid, params={'pn':pn}, headers=self.account.headers).text
                raw = re.search('<div class="p_postlist" id="j_p_postlist">.*</div>',raw,re.S).group()
            except(AttributeError):
                raw = None
                time.sleep(0.25)
            finally:
                retry_times-=1

        if raw:
            content = BeautifulSoup(raw,'lxml')
        else:
            self.log.error("Failed to get posts of {tid}".format(tid=tid))
            return post_list

        try:
            posts = content.find_all("div",{'data-field':True,'data-pid':True})
            for post_raw in posts:
                post = _Post()
                post.tid = tid

                text_raw = post_raw.find("div",id=re.compile('^post_content_\d+$'))
                post.text = ''.join(text_raw.strings).strip()

                user_sign = post_raw.find(class_='j_user_sign')
                if user_sign:
                    post.sign = user_sign["src"]
                else:
                    post.sign = None

                imgs_raw = text_raw.find_all("img",class_='BDE_Image')
                post.imgs = [i["src"] for i in imgs_raw]

                smileys_raw = text_raw.find_all('img',class_='BDE_Smiley')
                post.smileys = [i["src"] for i in smileys_raw]

                author_info = json.loads(post_raw["data-field"])
                post.pid = author_info["content"]["post_id"]
                post.user_name = author_info["author"]["user_name"]
                post.nick_name = author_info["author"]["user_nickname"]
                post.portrait = author_info["author"]["portrait"]
                post.level = int(post_raw.find('div',attrs={'class':'d_badge_lv'}).text)
                post.floor = author_info["content"]["post_no"]
                post.comment_num = author_info["content"]["comment_num"]

                post_list.append(post)

        except KeyError:
            self.log.error("KeyError: Failed to get posts of {tid}".format(tid=tid))
            return []
        else:
            return post_list

    def _get_comment(self,tid,pid,pn=1):
        """
        获取楼中楼回复
        _get_comment(tid,pid,pn=1)

        Returns:
            has_next: 是否还有下一页
            _Comment
        """   
        
        tid = str(tid)
        pid = str(pid)
        self._set_host(self.comment_url)
        raw = req.get(self.comment_url, params={'tid':tid,'pid':pid,'pn':pn}, headers=self.account.headers).text
        content = BeautifulSoup(raw,'lxml')
        comments = []
        try:
            raws = content.find_all('li',class_=re.compile('lzl_single_post'))
            has_next = True if content.find('a',string='下一页') else False

            for comment_raw in raws:
                comment = _Comment()
                comment_data = json.loads(comment_raw['data-field'])
                comment.pid = comment_data['spid']
                comment.tid = tid
                nick_name = comment_raw.find('a',class_='at j_user_card').text
                if nick_name == comment.user_name:
                    comment.nick_name = ''
                else:
                    comment.nick_name = nick_name

                text_raw = comment_raw.find('span',class_='lzl_content_main')
                comment.text = text_raw.text.strip()

                smileys_raw = text_raw.find_all('img',class_='BDE_Smiley')
                comment.smileys = [i["src"] for i in smileys_raw]

                comments.append(comment)

            return has_next,comments

        except KeyError:
            log.error("KeyError: Failed to get posts of {pid} in thread {tid}".format(tid=tid,pid=pid))
            return []

    def _new_del_thread(self,tb_name,tid):
        """
        新api，删主题帖
        _new_del_thread(tb_name,tid)
        """
        payload = {'commit_from':'pb',
                   'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._get_fid(tb_name),
                   'tid':tid
                   }
        self._set_host(self.new_del_thread_api)
        res = req.post(self.new_del_thread_api, data = payload, headers = self.account.headers).content.decode('unicode_escape')
        if re.search('"err_code":0',res):
            self.log.info("Delete thread {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
            return True
        else:
            self.log.warning("Failed to delete thread {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
            return False

    def _new_del_post(self,tb_name,tid,pid):
        """
        新api，删回复
        __new_del_post(tb_name,tid,pid)
        """
        payload = {'commit_from':'pb',
                   'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._get_fid(tb_name),
                   'tid':tid,
                   'is_vipdel':0,
                   'pid':pid,
                   'is_finf':'false'
                   }
        self._set_host(self.new_del_post_api)
        res = req.post(self.new_del_post_api, data = payload, headers = self.account.headers).content.decode('unicode_escape')
        if re.search('"err_code":0',res):
            self.log.info("Delete post {pid} in {tid} in {tb_name}".format(pid=pid,tid=tid,tb_name=tb_name))
            return True
        else:
            self.log.warning("Failed to delete post {pid} in {tid} in {tb_name}".format(pid=pid,tid=tid,tb_name=tb_name))
            return False