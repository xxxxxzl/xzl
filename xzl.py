#coding=utf8

import requests
from scrapy.selector import Selector
import time
import html2text as ht
import os
from selenium import webdriver
import pdfkit
import browsercookie

# 我们应该尊重每一位作者的付出， 请不要随意传播下载后的文件

# 由于采集目录时需要模拟鼠标滑动， 所以请打开Safari的允许远程自动化， 开发->允许远程自动化

# 小专栏基础地址
xzl = 'https://xiaozhuanlan.com'

# 设置等待时长
seconds = 3

# 文件标题是否添加文章编写时间
hasTime = True

# 是否以MarkDown格式导出, 导出pdf需先下载![wkhtmltopdf](https://wkhtmltopdf.org/downloads.html)
# mac可以直接通过 `brew install Caskroom/cask/wkhtmltopdf` 进行安装
markdown = True

# 当为小书时，且`markdown=False`，是否将所有章节进行拼接为一个pdf
xs_pdf = True

# 通过Chrome采集到账号cookie，模拟用户登录状态
# 此处不需要修改，将会自动从Chrome中获取cookie内容
headers = {
    'Cookie': ''
}


def fetch_cookie():
    """ 
    Fetch cookie from `cookie.cache`
    """
    global headers
    if os.path.exists('./cookie.cache'):
        with open('./cookie.cache', 'r') as cookie:
            headers['Cookie'] = cookie.read()
    else:
        chrome_cookie = browsercookie.chrome()
        for cookie in chrome_cookie:
            if cookie.name == '_xiaozhuanlan_session':
                xzl_session = cookie.name + '=' + cookie.value
                with open('./cookie.cache', 'w') as f:
                    f.write(xzl_session)
                headers['Cookie'] = xzl_session
        if not xzl_session:
            print('\n\n\n\n请先在Chrome上登录小专栏\n\n\n\n')


# 采集订阅列表
def get_subscribes():
    print('开始采集订阅列表\n')
    url = xzl + '/' + 'me/subscribes'
    driver = webdriver.Safari()
    driver.get(xzl)
    cookies = headers.get('Cookie').replace(' ', '').split(';')
    for cookie in cookies:
        cs = cookie.split('=')
        driver.add_cookie({'name': cs[0], 'value': cs[1]})
    driver.get(url)
    print('开始采集订阅目录， 采集完成后自动关闭浏览器\n')
    style = ''
    while not style == 'display: block;':
        print('正在采集。。。\n')
        time.sleep(seconds)
        # 此处模拟浏览器滚动， 以采集更多数据
        js = "window.scrollTo(0, document.documentElement.scrollHeight*2)"
        driver.execute_script(js)
        style = driver.find_element_by_class_name('xzl-topic-list-no-topics').get_attribute('style')
    selector = Selector(text=driver.page_source)
    items = selector.css(u'.streamItem-cardInner').extract()
    print('列表采集完成，共找到%d条数据\n'%len(items))
    for item in items:
        selector = Selector(text=item)
        href = selector.css(u'.zl-title a::attr(href)').extract_first()
        title = selector.css(u'.zl-title a::text').extract_first()
        book = selector.css('.zl-bookContent').extract_first()
        print('开始采集: ' + title + '的目录信息\n')
        if book:
            print('当前内容为小书\n')
            get_xs(href, True)
        else:
            print('当前内容为专栏\n')
            get_zl(href, driver)
        time.sleep(seconds)
    print('所有内容已导出完成，我们应该尊重每一位作者的付出，请不要随意传播下载后的文件\n')


# 采集小书章节目录
def get_xs(href, is_all=False):
    url = xzl + href + '#a4'
    print('开始采集小书信息，小书地址为: ' + url + '\n')
    xzl_path = ''
    if is_all:
        xzl_path = '小专栏/'
    response = close_session().get(url=url, headers=headers)
    selector = Selector(text=response.text)
    chapter = selector.css(u'.book-cata-item').extract()
    xs_title = selector.css(u'.bannerMsg .title ::text').extract_first()
    html = ''
    if xs_pdf:
        html = '<div>' + selector.css(u'.dot-list').extract_first() + '</div>'
    for idx, c in enumerate(chapter):
        selector = Selector(text=c)
        items = selector.css(u'.cata-sm-item').extract()
        z_title = selector.css(u'a::text').extract_first()
        z_href = selector.css(u'a::attr(href)').extract_first()
        path = os.path.join(os.path.expanduser("~"), 'Desktop')+'/'+xzl_path+xs_title+'/'+z_title+'/'
        if xs_pdf:
            path = os.path.join(os.path.expanduser("~"), 'Desktop')+'/'+xzl_path+xs_title+'/'
        else:
            print(xs_title + '共%d章, 正在创建存储目录\n' % len(chapter))
            print('文件存储位置: ' + path + '\n')
        if not os.path.exists(path):
            os.makedirs(path)
            print('文件夹创建成功\n')
        html += get_xs_detail(z_href, z_title, path)
        for item in items:
            selector = Selector(text=item)
            j_title = selector.css(u'.cata-sm-item a::text').extract_first()
            j_href = selector.css(u'.cata-sm-item a::attr(href)').extract_first()
            html += get_xs_detail(j_href, j_title, path)
            time.sleep(seconds)
        time.sleep(seconds)
    if xs_pdf:
        # 在html中加入编码， 否则中文会乱码
        html = "<html><head><meta charset='utf-8'></head> " + html + "</html>"
        pdfkit.from_string(html, path+xs_title+'.pdf')
    print('小书：' + xs_title + '的文章已采集完成\n')
    print('我们应该尊重每一位作者的付出， 请不要随意传播下载后的文件\n')


# 采集小书章节详情
def get_xs_detail(href, title, path):
    url = xzl+href
    print('开始采集' + title + '的详情, 章节地址为: ' + url + '\n')
    text_maker = ht.HTML2Text()
    response = close_session().get(url=url, headers=headers)
    selector = Selector(text=response.text)
    html = selector.css(u'.cata-book-content').extract_first()
    file_name = title
    if markdown:
        md = text_maker.handle(html)
        with open(path + file_name + '.md', 'w') as f:
            f.write(md)
    else:
        if not xs_pdf:
            # 在html中加入编码， 否则中文会乱码
            html = "<html><head><meta charset='utf-8'></head> " + html + "</html>"
            pdfkit.from_string(html, path + file_name + '.pdf')
        else:
            return html


# 采集专栏列表
def get_zl(href, driver=None):
    url = xzl + href
    print('开始采集专栏信息，专栏地址为: ' + url + '\n')
    xzl_path = ''
    if not driver:
        driver = webdriver.Safari()
        driver.get(xzl)
        cookies = headers.get('Cookie').replace(' ', '').split(';')
        for cookie in cookies:
            cs = cookie.split('=')
            driver.add_cookie({'name': cs[0], 'value': cs[1]})
    else:
        xzl_path = '小专栏/'
    driver.get(url)
    print('开始采集专栏文章目录\n')
    style = ''
    while not style == 'display: block;':
        print('正在采集。。。\n')
        time.sleep(seconds)
        # 此处模拟浏览器滚动， 以采集更多数据
        js = "window.scrollTo(0, document.documentElement.scrollHeight*2)"
        driver.execute_script(js)
        style = driver.find_element_by_class_name('xzl-topic-list-no-topics').get_attribute('style')
    selector = Selector(text=driver.page_source)
    items = selector.css(u'.topic-body').extract()
    print('采集文章数量: %d篇\n'%len(items))
    zl_title = selector.css(u'.zhuanlan-title ::text').extract_first().replace('\n', '').replace(' ', '')
    print('目录采集完成, 正在采集的专栏为: ' + zl_title + ', 开始为您创建存储路径\n')
    path = os.path.join(os.path.expanduser("~"), 'Desktop') + '/' + xzl_path + zl_title + '/'
    print('文件存储位置: ' + path + '\n')
    if not os.path.exists(path):
        os.makedirs(path)
        print('文件夹创建成功\n')
    print('开始采集文章详情\n')
    for idx, item in enumerate(items):
        selector = Selector(text=item)
        link = selector.css(u'a::attr(href)').extract_first()
        title = selector.css(u'h3::text').extract_first().replace('\n', '').replace(' ', '').replace('/', '-')
        detail_url = xzl+link
        print('开始采集文章: ' + title + ', 文章地址为: ' + detail_url + '\n')
        get_zl_detail(detail_url, path, title)
        # 延迟三秒后采集下一文章
        time.sleep(seconds)
    print('专栏：' + zl_title + '的文章已采集完成' + '\n')
    print('我们应该尊重每一位作者的付出， 请不要随意传播下载后的文件\n')


# 采集专栏详情
def get_zl_detail(url, path, name):
    response = close_session().get(url=url, headers=headers)
    selector = Selector(text=response.text)
    text_maker = ht.HTML2Text()
    create_time = selector.css(u'.time abbr::attr(title)').extract_first()
    html = selector.css(u'.xzl-topic-body-content').extract_first()
    file_name = name
    if hasTime:
        file_name = create_time+' '+name
    if markdown:
        md = text_maker.handle(html)
        with open(path + file_name + '.md', 'w') as f:
            f.write(md)
    else:
        # 在html中加入编码， 否则中文会乱码
        html = "<html><head><meta charset='utf-8'></head> " + html + "</html>"
        pdfkit.from_string(html, path + file_name + '.pdf')


# 关闭多余连接
def close_session():
    request = requests.session()
    # 关闭多余连接
    request.keep_alive = False
    return request


if __name__ == '__main__':
    print('我们应该尊重每一位作者的付出， 请不要随意传播下载后的文件\n')
    print('当浏览器自动打开后，请勿关闭浏览器，内容采集、导出完成后将会自动关闭\n')
    # 增加重连次数
    # requests.adapters.DEFAULT_RETRIES = 5
    # 获取cookie
    fetch_cookie()
    # 采集小书
    # 专栏地址，仅填写最后一位即可，如：https://xiaozhuanlan.com/ios-interview, 填写/ios-interview即可
    # get_xs('/ios-interview')
    # 采集专栏
    # 专栏地址，仅填写最后一位即可，如：https://xiaozhuanlan.com/The-story-of-the-programmer, 填写/The-story-of-the-programmer即可
    get_zl('/The-story-of-the-programmer')
    # 采集全部订阅内容
    # get_subscribes()


