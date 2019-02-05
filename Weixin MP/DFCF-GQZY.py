#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 先导入三个包，分别是
# 系统相关的os
# 网络访问的requests，如果没安装请pip install 安装
# 正则表达式re
import os, requests, re
# 对url进行编码需要用到
from urllib import parse

# 先获取相应的参数
# 主要思路
# type和token在网页中提取。网址http://data.eastmoney.com/gpzy/pledgeDetail.aspx
# cmd是空值
# st 表示的排列顺序（sort type），升序降序之类的，取默认值
# sr 表示的排列规则（sort rule），按哪个变量排，取默认值
# p 表示第几页，循环代入
# ps 表示每页有几个观测值（几行），保持默认值
# js var DZCmUvYm={pages:(tp),data:(x),font:(font)}，这个是请求数据的返回形式，我们把变量名字DZCmUvYm改一下（不改也可以），比如叫FDMT
# js var FDMT={pages:(tp),data:(x),font:(font)}
# filter=(datatype=1)，保持不变
# rt=51631614，时间从python中生成或者请求，从python中生成，如果系统时间有问题，就会出现访问错误
# 考虑到rt的获取只需要一次，稳妥起见，我们从以下url获取。
# http://blog.eastmoney.com/timezone.aspx
# 还有就是总的页数这个参数，这个参数隐含在返回的json数据中。
# 所以我们先对第一页进行提取并解析，而后续的部分，我们将提取和解析分为两步进行
# 万事具备，获取参数的部分可以先写了
def getParam():
    # 设置headers可以在一定程度上防止被网站河蟹
    # 浏览器UA信息可以从网上找或者看自己浏览器对应的UA。
    headers = {
        'Accept-Encoding':'gzip, deflate',
        'Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
    }

    # 如果要用到代理服务器，则填写代理服务器信息
    proxies = {
        # 'http':'1.2.3.4:80',
        # 'https':'1.2.3.4:80'
    }

    # 获取数据网页的url地址如下
    url1 = 'http://data.eastmoney.com/gpzy/pledgeDetail.aspx'

    # 发送请求，如果没有用到代理服务器，就不要写proxies = proxies
    r = requests.get(url = url1, headers = headers, proxies = proxies,  timeout = 5)
    # 查看返回状态和返回的内容
    print(r.status_code)
    # 如果返回200，说明网页成功获取，否则获取失败
    # 我们这里简单粗暴一点，如果获取失败，直接退出
    if r.status_code != 200:
        print('无法连接至%s！' %url1)
        return
    # print(r.text)
    webpage = r.text
    # 查看返回内容主要是看中文是不是存在乱码
    # 提取type和token参数
    # 用正则表达式
    # token参数在网页中的位置是 &token=70f12f2f4f091e459a279469fe49eca5&cmd
    # 正则匹配大小写字母+数字串（不会的请自行学习正则表达式）
    # 注意这里最好用懒惰模式，尽量匹配最短的
    regx1 = re.compile(r'\&token=([A-Za-z0-9]*?)&cmd')
    token = regx1.findall(webpage)
    print(token)
    # 显示的应该是形如['70f12f2f4f091e459a279469fe49eca5']（每个人token不一样）
    # 查看一下，正常应该只有一个符合要求，我们直接把这个值赋给token
    token = token[0]
    # 同样的方法提取type，注意type是包含字母+下划线。所以我们用[a-zA-Z]\w来做正则匹配
    # type与函数type有重复，所以我们大写开头字母
    # 这里也最好用懒惰模式，尽量匹配最短的
    regx2 = re.compile(r'type\=([a-zA-Z]\w*?)\&token')
    Type = regx2.findall(webpage)[0]
    print(Type)

    # 从http://blog.eastmoney.com/timezone.aspx获取时间
    url2 = 'http://blog.eastmoney.com/timezone.aspx'
    r2 = requests.get(url = url2, headers = headers, proxies = proxies,  timeout = 5)
    # 同样简单粗暴，如果获取失败，直接退出
    if r2.status_code != 200:
        print('无法连接至%s！' %url2)
        return
    realtime = r2.text
    # print('无法连接至：%s' %url2)
    print(realtime)
    # 返回的是var bjTime = 1548985495
    # 我们只要数字，正则匹配数字，当然这里用的贪婪模式。
    regx3 = re.compile(r'var bjTime = ([0-9]*)')
    rt = regx3.findall(realtime)
    print(rt)

    # 把这些参数打包成一个字典返回，则除了循环带入的页数参数外
    # 其他动态调整的参数全部获取完毕
    param = {
        'Type': Type,
        'token': token,
        'rt': rt
    }
    return param
# 参数已经获得完毕，现在就是写如何获得每一页返回的数据
# 要输入一个参数——佩奇（page），告诉爬虫获取第几页的内容
# 这里要注意，我们这个获取某一页返回数据的函数，最后是要放在一个循环中
# 每次循环使用的如token rt之类的参数都要一样，这样能保证我们提取到的数据是一致的
# 所以我们除了佩奇之外，还要输入type token rt这三个参数
# 我们需要提取第一页中的总页数这一数据
# PATH是我们保存所下载数据的路径，默认是系统临时文件夹下的pytemp
# 我们在这一部分中，只是完成下载的工作，不做解析，这样的好处是在网络情况不太稳定时
# 能够保证下载的完整性和解析的准确性
def getJson(page, Type, token, rt, path = os.environ["TMP"] + '\\pytemp\\json\\'):
    # 先检查有没有path对应的路径，如果没有就生成
    if os.path.exists(path) == False:
        os.makedirs(path)
    # 先构建参数
    # ps可以更改成更大的数字，以增加每次请求获取的记录条数。
    paramdata = {
        'type': Type,
        'token': token,
        'cmd':'' ,
        'st': 'ndate',
        'sr': '-1',
        'p': str(page),
        'ps': '50',
        'js': 'var FDMT={pages:(tp),data:(x),font:(font)}',
        'filter': '(datatype=1)',
        'rt': rt
    }
    proxies = {
        # 'http':'1.2.3.4:80',
        # 'https':'1.2.3.4:80'
    }
    # 把url的前面部分和data完成合并
    # 用urllib中的parse
    # url前段是
    urlp = 'http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get?'
    # 对参数进行url编码
    urlpar = parse.urlencode(paramdata)
    # 合并url
    pageurl = urlp + urlpar
    # 如果不放心可以看一下生成的pageurl是不是可以访问
    # print(pageurl)
    # 有了URL之后，可以直接获取json数据
    headers = {
        'Accept-Encoding':'gzip, deflate',
        'Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
    }
    r3 = requests.get(url = pageurl, headers = headers, proxies = proxies,  timeout = 5)
    if r3.status_code != 200:
        print('无法连接至第%s页的数据！' %(str(page)))
        return
    with open(path + 'j%s.txt' %str(page) ,'w+', encoding = 'utf-8') as f:
        f.write(r3.text)
    print('第%s页的数据下载成功！' %(str(page)))
    # 如果是第一页，顺便解析出总页数
    if page == 1:
        # 用正则表达式检索，用懒惰模式
        # var FDMT={pages:1352,
        regx4 = re.compile(r'{pages:([0-9]*?)\,')
        tpages =regx4.findall(r3.text)[0]
        # print(tpages)
        return tpages
    else:
        return 1

# 写完获取单个页面上的json数据，我们就可以写循环和批量解析了
# 按照稳定性优先的原则，我们还是先获取数据，并保存到本地，然后再批量解析
def getJsons(path = os.environ["TMP"] + '\\pytemp\\'):
    canshu = getParam()
    Type = canshu['Type']
    token = canshu['token']
    rt = canshu['rt']
    # 总页数
    tpages = eval(getJson(1, Type, token, rt))
    # 这里我们生成一个下载列表，下载成功，从列表中去除，如果不成功，就保留。直到列表为空
    downloadlist = range(1, tpages + 1)
    while len(downloadlist) > 0:
        # 生成一个错误列表，记录不成功的下载记录
        errlist = []
        for i in downloadlist:
            # 试着获取参数
            try:
                # getJson如果是第一页，会返回总页数，如果是其他页，会返回1，错误就是None
                xiazai = getJson(i, Type, token, rt)
            except:
                errlist.append(i)
                continue
            if xiazai is None:
                errlist.append(i)
                continue
        downloadlist = errlist
    print('所有数据已下载完毕，共%s条！' %(str(tpages)))
    # 最后返回tpages共解析使用
    return tpages

# 写解析模块
def dataClean(path = os.environ["TMP"] + '\\pytemp\\', resultpath = 'E:\\python\\'):
    # 先检查有没有path对应的路径，如果没有就生成
    if os.path.exists(path) == False:
        os.makedirs(path)
    # tpages = getJsons()
    tpages = 1356
    # 设一个dataframe记录结果
    colname = []
    # 设一个变量记录总记录数
    m = 0
    resultlst = []
    for i in range(1,tpages+1):
        # 读取json数据
        with open(path + 'json\\j%s.txt' %(str(i)),'r',encoding = 'utf-8') as f:
            json = f.read()
        # 读出来的是
        # var FDMT={pages:1353,data:[{""}],font:}
        # 为了防止后续处理出现断行等问题，先替换一批特殊字符
        json = json.replace('\r\n','',len(json))
        json = json.replace('\n','',len(json))
        # 先把FDMT=之后的数据提取出来，这里用贪婪模式
        regx5 = re.compile(r'=({.*})')
        dicl1 = regx5.findall(json)[0]
        # 我们按python字典的要求先把 pages data font 加上''
        dicl1 = dicl1.replace('pages','\'pages\'',1)
        dicl1 = dicl1.replace('data','\'data\'',1)
        dicl1 = dicl1.replace('font','\'font\'',1)
        # 转换成dic
        dicl1 = eval(dicl1)
        # 如果能提取出来pages，就说明成功了
        # print(dicl1['pages'])
        # 我们要提取font中的fontMapping，用来解码
        font = dicl1['font']
        keys = font['FontMapping']
        # print(keys)
        # 我们要的是data字段的内容
        data = dicl1['data']
        # print(data)
        # 注意到data是个list里面是一个个小的dict
        # 不论怎样，我们先将data变成字符串，I换掉里面用自定义字符显示的数字
        datastr = str(data)
        for key in keys:
            datastr = datastr.replace(key['code'],str(key['value']),len(datastr))
        data = eval(datastr)
        # 循环提取，存为字符串，最后保存成csv
        # 记录处理的条数
        k = 0
        csv = ''
        for dic in data:
            k = k + 1
            m = m + 1
            # gdmc = dic['gdmc'].strip()
            # gdmc = gdmc.replace(',','、',9999999)
            # jgmc = dic['jgmc'].strip()
            # jgmc = jgmc.replace(',',' ',len(jgmc))
            # frozenreason = dic['frozenreason'].strip()
            # frozenreason = frozenreason.replace(',','，',len(frozenreason))
            # 给每一项都加上""，可以防止该项中包含,等情况导致csv分段错误的情况。
            csv = csv + '\n"' + dic['scode'] + '","' + dic['sname'] + '","' + dic['gdmc'] + '","' + dic['sharefrozennum'] \
                + '","' + dic['frozenratio'] + '","' + dic['frozenintotal'] + '","' + dic['jgmc'] + '","' + dic['jg_sname'] \
                + '","' + dic['jglx'] + '","' + dic['newprice_new'] + '","' + dic['spj'] + '","' + dic['pcx'] \
                + '","' + dic['sdate'] + '","' + dic['ndate'] + '","' + dic['frozenreason'] + '"'
        print('第{0}页数据已处理完毕，共{1}页'.format(str(i),str(tpages)))
        with open(path+str(i)+'.csv','w+', encoding = 'gbk') as f:
            f.write(csv)
        resultlst.append(csv)
    csv = '股票代码,股票简称,股东名称,质押股份数量,占所持股份比例,占总股本比例,质押机构,机构简称,机构类型,最新价,质押日收盘价,预估平仓线,质押开始日期,公告日期,质押原因'
    n = 0
    for result in resultlst:
        n = n + 1
        print('正在合并%s项' %str(n))
        csv = csv + result
    with open(resultpath + '结果.csv','w+', encoding = 'gbk') as f:
        f.write(csv)
    print('所有记录已处理完毕，共%s条！' %(str(len(resultlst))))


# dataClean()
# print(conv('&#xE426;&#xF78F;&#xE712;&#xE891;'))

dataClean(resultpath = 'E:\\python\\')