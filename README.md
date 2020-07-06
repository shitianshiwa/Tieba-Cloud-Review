# Tieba-Cloud-Review
部署于Linux服务器的百度贴吧云审查脚本
## 功能特点
### 优点
+ 基于网页版贴吧和部分客户端版本的api，支持小吧封十天
+ 得益于Python语言的强大扩展能力，现已支持二维码识别
+ 自定义修改函数，不再拘束于傻瓜式脚本的关键词组合，而是可以定义复杂的正则表达式，从用户等级/评论图片等等方面入手判断删帖与封禁条件
### 缺点
- 需要一定的Python&Linux编程基础
- 需要大量依赖项，脚本部署困难
## 如何部署
部署过程由难到易，如果第一步你就做不下去建议放弃使用该脚本
1. 下载压缩包并在任一目录里解包，目录示例：/root/scripts/tieba
2. 配置MySQL
    + 数据库用于缓存通过检测的带图回复的pid，以节约图像检测的耗时
    + 打开./browser/_browser.py
        + 修改开头的DB_NAME可指定数据库名
        + 修改mysql_login来连接到你的MySQL数据库
3. pip安装需要的Python库
    ```
    sudo pip3 install mysql-connector
    sudo pip3 install lxml
    sudo pip3 install bs4
    sudo pip3 install pillow
    ```
