#!/usr/bin/env python
# -*- coding:utf-8 -*-
__all__ = ('BlockID',)

import re
import pickle

import requests as req

from ._browser import _Browser

class BlockID(_Browser):
    """
    提供百度贴吧定向封禁功能
    BlockID(self,headers_filepath:str,admin_type:int)

    参数:
        headers_filepath: 字符串 消息头文件路径
        admin_type: 整型 吧务权限最高允许的封禁天数
    """

    def __init__(self,headers_filepath:str,admin_type:int):
        super(BlockID,self).__init__(headers_filepath)
        try:
            self.admin_type = admin_type if admin_type in [1,10] else 1
        except AttributeError:
            raise(AttributeError('Incorrect format!'))

        self.old_block_content = {'BDUSS':self.account.cookies['BDUSS'],
                                    'day':1,
                                    'fid':'',
                                    'ntn':'banid',
                                    'reason':'null',
                                    'tbs':'',
                                    'un':'',
                                    'word':'',
                                    'z':'4623534287'
                                    }

    def quit(self):
        super(BlockID,self).quit()

    def _old_block(self,block):
        """
        使用旧版api的封禁，适用于权限不足的情况，且被封禁用户必须有用户名
        """

        try:
            self.old_block_content['day'] = block['day']
            self.old_block_content['fid'] = self._get_fid(block['tb_name'])
            self.old_block_content['tbs'] = self._get_tbs()
            self.old_block_content['un'] = block['user_name']
            self.old_block_content['word'] = block['tb_name']
        except AttributeError:
            self.log.error('AttributeError: Failed to block!')

        sign = self._get_sign(self.old_block_content)
        self.old_block_content['sign'] = sign

        res = req.post(self.old_block_api,self.old_block_content).content.decode('unicode_escape')
        del self.old_block_content['sign']

        if re.search('"error_code":"0"',res):
            self.log.info('Success blocking {name} in {tb_name} for {day} days'.format(name=block['user_name'],tb_name=block['tb_name'],day=self.old_block_content['day']))
        else:
            self.log.warning('Failed to block {name} in {tb_name}'.format(name=block['user_name'],tb_name=block['tb_name']))


    def _new_block(self,block,name_type:str='username'):
        """
        使用新版api的封禁，适用于权限充足或需要封禁无用户名用户（仅有带emoji昵称）的情况
        """

        new_block_content = {"ie":"gbk"}
        new_block_content['reason'] = block['reason'] if block.__contains__('reason') else 'null'

        try:
            new_block_content['day'] = block['day'] if block['day'] < self.admin_type else self.admin_type
            new_block_content['fid'] = self._get_fid(block['tb_name'])
            new_block_content['tbs'] = self._get_tbs()
        except AttributeError:
            self.log.error('AttributeError: Failed to block!')

        if block.get('user_name',''):
            name = block['user_name']
            new_block_content['user_name[]'] = block['user_name']
        elif block.get('nick_name',''):
            name = block['nick_name']
            new_block_content['nick_name[]'] = block['nick_name']
            if block.get('portrait',''):
                new_block_content['portrait[]'] = block['portrait']
            else:
                try:
                    new_block_content['portrait[]'] = self._get_portrait(name)
                except AttributeError:
                    self.log.warning('{user_name}已被屏蔽'.format(user_name=name))
                    return True
        else:
            self.log.warning('Failed to block {user_name} in {tb_name}'.format(tb_name=block['tb_name'],user_name=name))
            return False

        res = req.post(self.new_block_api,new_block_content,headers=self.account.headers).content.decode('unicode_escape')
        if re.search('"errno":0',res):
            self.log.info('Success blocking {name} in {tb_name} for {day} days'.format(name=name,tb_name=block['tb_name'],day=new_block_content['day']))
        else:
            self.log.warning('Failed to block {name} in {tb_name}'.format(name=name,tb_name=block['tb_name']))


    def block(self,block):
        """
        根据需求自动选择api进行封禁，以新版api为优先选择
        block(self,block)

        参数:
            block:封禁请求
                举例: 
                {'tb_name':'吧名',
                'user_name':'用户名',
                'nick_name':'昵称',
                'day':'封禁天数,
                'portrait':'portrait（可选）',
                'reason':'封禁理由（可选）'
                }
        """

        if block['day'] > self.admin_type and block['user_name']:
            self._old_block(block)
        else:
            self._new_block(block)