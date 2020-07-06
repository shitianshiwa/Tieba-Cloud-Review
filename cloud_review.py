#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import time
import argparse

import re
import json
import browser

PATH = os.path.split(os.path.realpath(__file__))[0].replace('\\','/')

class CloudReview(browser._CloudReview):
    def __init__(self,headers_filepath,ctrl_filepath):
        super(CloudReview,self).__init__(headers_filepath,ctrl_filepath)

    def quit(self):
        super(CloudReview,self).quit()

    def __check_thread(self,thread):
        """
        检查thread内容
        """
        if re.search(re.compile('python_test|破解版'),thread.topic):
            return True
        if re.search(re.compile('揭秘.*霸服'),thread.topic):
            self.block({'tb_name':self.tb_name,'user_name':thread.user_name,'nick_name':thread.nick_name,'portrait':thread.portrait,'day':10})
            return True

        posts = self._get_posts(thread.tid,9999)
        for post in posts:
            if self.__check_post(post) == 1:
                self.log.info("Try to delete reply post by {user_name}/{nick_name}".format(user_name=post.user_name,nick_name=post.nick_name))
                self._new_del_post(self.tb_name,post.tid,post.pid)
            elif self.__check_post(post) == 2:
                if posts[0].floor == 1 and post.user_name == posts[0].user_name:
                    self.block({'tb_name':self.tb_name,'user_name':post.user_name,'nick_name':post.nick_name,'portrait':post.portrait,'day':10})
                    return True
        return False

    def __check_post(self,post):
        """
        检查回复内容
        """
        if re.search(re.compile('上车玩福利|兼职|学习绘画.*加我|招募.*私信|(摄影|剪辑|后期|CAD|交流学习|素描|彩铅|[Pp][Ss]).*(群|课程|邮箱)|手游.*(神豪|托|演员)|鲁迅.*神秘的数字|饿了么运营|拿提成|家族口号：老兵不死，战斗不息|在家就可以做'),post.text) and post.level < 6:
            self.block({'tb_name':self.tb_name,'user_name':post.user_name,'nick_name':post.nick_name,'portrait':post.portrait,'day':10})
            return 1
        if re.search(re.compile('@(小度🎁活动🔥|小度º活动君|活动🔥小度🎁)'),post.text):
            return 2
        return 0

    def run_review(self):
        while self.cycle_times != 0:
            threads = self._get_threads(self.tb_name)
            for thread in threads:
                if self.__check_thread(thread):
                    self.log.info("Try to delete thread post by {user_name}/{nick_name}".format(user_name=thread.user_name,nick_name=thread.nick_name))
                    self._new_del_thread(self.tb_name,thread.tid)

            review_control = self._link_ctrl_json(self.ctrl_filepath)
            if review_control.get('quit_flag',False):
                self.log.debug("Quit the program controlled by cloud_review.json")
                return
            elif self.cycle_times >= 0:
                self.cycle_times-=1
            if self.sleep_time:
                time.sleep(self.sleep_time)
        self.log.debug("Quit the program controlled by cycle_times")


parser = argparse.ArgumentParser(description='Scan tieba threads')
parser.add_argument('--review_ctrl_filepath', '-rc',type=str,default=PATH + '/user_control/' + browser.SHOTNAME + '.json', help='path of the review control json | default value for example.py is ./user_control/example.json')
parser.add_argument('--header_filepath', '-hp',type=str,default=PATH + '/user_control/headers.txt', help='path of the headers txt | default value is ./user_control/headers.txt')
kwargs = vars(parser.parse_args())

review = CloudReview(kwargs['header_filepath'],kwargs['review_ctrl_filepath'])
review.run_review()
review.quit()