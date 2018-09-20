#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib.request
import sys, io, os
import re
from bs4 import BeautifulSoup
from distutils.filelist import findall
import pandas as pd
import numpy as np
# 显示系统正在使用的编码方式
print(sys.stdout.encoding)
# 显示目前在用的目录
print(os.getcwd())

# 加一个代理服务器的函数
def use_proxy(proxy_addr,url):
    try:
        #设置代理服务器
        proxy = urllib.request.ProxyHandler({'http':proxy_addr})
        #创建对象
        opener = urllib.request.build_opener(proxy)
        #创建全局默认的对象
        urllib.request.install_opener(opener)
        #读取数据
        webpage = urllib.request.urlopen(url).read().decode('utf-8')
        return webpage
    except:
        print('无法链接服务器！！！')

# 建立一个函数，便与后续用于其他的类似任务的调用。
# 这个函数要输入：
    # 因为要用到代理服务器，所以要多引进一个代理服务器地址的变量（proxy）
    # url中不会随着页码变化的部分（urlprefix和urlsuffix）；
    # 数据存放的本地目录（dataset，需要事先建好）；
    # 保存数据文件的命名规则，这里就是前缀（tmpprfx）加上网页的页码；
    # 生成表格的表头，也是dataframe的列名称（colname）；
    # 最后保存出来的csv的名字（savename）。

def fkds(proxy, urlprefix, urlsuffix, dataset, tmpprfx, colname, savename):
    aurl = urlprefix + '1' + urlsuffix 
    webpage = use_proxy(proxy, aurl)
    soup = BeautifulSoup(webpage,"html.parser")
    page_num_block = soup.find('div',class_='page')
    page_num_list = re.findall(r'\d+',page_num_block.get_text().strip())
    print('共',page_num_list[0],'页及',page_num_list[1],'个观测值需要下载')
    tp = int(page_num_list[0]) + 1
    to = int(page_num_list[1])
    for i in range (1,tp):
        i_str=str(i)
        burl = urlprefix + i_str + urlsuffix
        webpage = use_proxy(proxy, burl)
        filename= dataset + '/' + tmpprfx + i_str + '.txt'
        f = open(filename, "w", encoding='utf-8')
        print ('文件名为: ', f.name)
        f.write(webpage)
        f.close()

    df = pd.DataFrame(columns=colname)
    for i in range(1,tp):
        rnum = 0
        df1 = pd.DataFrame(columns=colname)
        i_str=str(i)
        filename = dataset + '/' + tmpprfx + i_str + '.txt'
        webpage = open(filename, 'r', encoding='utf-8')
        print('已读取：', webpage.name)
        soup = BeautifulSoup(webpage,"html.parser")
        for tr in soup.find_all('tr', class_='timeborder'):
            cnum = 0
            for td in tr.find_all('td'):
                df1.loc[rnum,colname[cnum]]=td.get_text().strip()
                cnum = cnum + 1
            for k in tr.find_all('a'):
                link = 'http://ipo.csrc.gov.cn' + '/' + k['href']
                df1.loc[rnum,'PDF链接'] = link
            rnum = rnum + 1
        df = pd.concat([df, df1], axis=0)
        print('第', i, '页', '已完成')
    if len(df) == to:
        print('经校对，共有', len(df),'条记录')
        savenamefull = dataset + '/' + savename + '.csv' 
        print(savenamefull)
        df.to_csv(savenamefull, encoding='gbk', index=False)
    else:
        print('已提取',len(df), '条记录，但总共有',to, '条需要提取。存在错误，请检验')

# 这里把变量名称与函数fkds的参数名称进行了区分
proxy_addr = '1.2.3.4:8080' 
urlpre = 'http://ipo.csrc.gov.cn/infoBlock.action?pageNo='
urlsuf = '&temp=&temp1=&blockId=1&block=1&blockType=byBlock'
datafileset = 'E:/py/data/fkds'
filenameprfx='fkds'
colnm = ['公司名称','披露日期','上市地和板块','保荐机构','披露类型','PDF资料','PDF链接']
savefilen = 'Result'
fkds(proxy_addr, urlpre, urlsuf, datafileset, filenameprfx, colnm, savefilen)

