#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Author: Starry
@License: MIT
@Homepage: https://github.com/Starry-OvO
@Required Modules:
    sudo pip3 install mysql-connector
    sudo pip3 install lxml
    sudo pip3 install bs4
    sudo pip3 install pillow

    可能需要的第三方yum源: Raven(https://centos.pkgs.org/8/raven-x86_64/raven-release-1.0-1.el8.noarch.rpm.html)
    使用 [rpm -Uvh xxx.rpm] 来安装Raven源
    用 [sudo yum install zbar-devel] 来安装zbar支持
    用 [sudo pip install pyzbar] 来安装pyzbar
"""

from .block_id import BlockID
from .cloud_review import _CloudReview
from ._browser import SCRIPT_PATH,FILENAME,SHOTNAME