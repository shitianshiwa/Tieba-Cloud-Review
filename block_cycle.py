#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import time
import argparse

import json
import browser

PATH = os.path.split(os.path.realpath(__file__))[0].replace('\\','/')

parser = argparse.ArgumentParser(description='Block Tieba ID')
parser.add_argument('--admin_type','-at',
                    type=str,
                    default=1,
                    help='max blocking days of the admin account')
parser.add_argument('--block_ctrl_filepath','-bc',
                    type=str,
                    default=PATH + '/user_control/' + browser.SHOTNAME + '.json',
                    help='path of the block control json | default value for example.py is ./user_control/example.json')
parser.add_argument('--header_filepath','-hp',
                    type=str,
                    default=PATH + '/user_control/headers.txt',
                    help='path of the headers txt | default value is ./user_control/headers.txt')
kwargs = vars(parser.parse_args())

try:
    with open(kwargs['block_ctrl_filepath'],'r',encoding='utf-8-sig') as block_ctrl_file:
        block_control = json.loads(block_ctrl_file.read())
    block_list = block_control['block_list']
except FileExistsError:
    raise(FileExistsError('block control json not exist! Please create it!'))
except AttributeError:
    raise(AttributeError('Incorrect format of block_control.json!'))

try:
    admin_type = kwargs['admin_type']
except AttributeError:
    print('Please input the admin_type!')
    admin_type = 1

block_id = browser.BlockID(kwargs['header_filepath'],admin_type)

for block in block_list:
    block_id.block(block)
    time.sleep(1)
block_id.quit()