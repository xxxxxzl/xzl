import requests
from scrapy.selector import Selector
import time
import html2text as ht
import os
from selenium import webdriver
import pdfkit

# 我们应该尊重每一位作者的付出， 请不要随意传播下载后的文件

# 由于获取目录时需要模拟鼠标滑动， 所以请打开Safari的允许远程自动化， 开发->允许远程自动化

# 小专栏基础地址
xzl = 'https://xiaozhuanlan.com'

# 通过Chrome获取到账号cookie， 模拟用户登录状态
headers = {
    'Cookie': 'cookie'
}

# 文件标题是否添加文章编写时间
hasTime = True

# 一直下载失败。。。 有时间再搞
# 是否以MarkDown格式导出, 导出pdf需先下载![wkhtmltopdf](https://wkhtmltopdf.org/downloads.html)
# mac可以直接通过 `brew install Caskroom/cask/wkhtmltopdf` 进行安装
markdown = True

def start(name):
    url = xzl + "/" + name
    print('开始获取' + name + '的小专栏， 专栏地址为: ' + url)
    driver = webdriver.Safari()
    driver.get(url)
    print('\n开始采集作者文章目录， 采集完成后自动关闭浏览器')
    style = ''
    while not style == 'display: block;':
        print('正在采集。。。\n')
        time.sleep(2)
        # 此处模拟浏览器滚动， 以获取更多数据
        js = "window.scrollTo(0, document.documentElement.scrollHeight*2)"
        driver.execute_script(js)
        style = driver.find_element_by_class_name('xzl-topic-list-no-topics').get_attribute('style')
    print('目录采集完成, 开始获取文章详情详情\n')
    selector = Selector(text=driver.page_source)
    driver.quit()
    print('关闭临时浏览器\n')
    items = selector.css(u'.topic-body').extract()
    print('获取文章数量: ' + str(len(items)))
    path = os.path.join(os.path.expanduser("~"), 'Desktop') + '/' + name + '/'
    print('\n文件存储位置: ' + path)
    if not os.path.exists(path):
        os.makedirs(path)
        print('文件夹创建成功')
    for idx, item in enumerate(items):
        selector = Selector(text=item)
        link = selector.css(u'a::attr(href)').extract_first()
        title = selector.css(u'h3::text').extract_first().replace('\n', '').replace(' ', '')
        detail_url = xzl+link
        print('开始获取文章: ' + title + ', 文章地址为: ' + detail_url + '\n')
        get_detail(detail_url, path, title)
        # 延迟三秒后获取下一文章
        time.sleep(3)
    print('小专栏作者' + name + '的文章已获取完成' + '\n')
    print('我们应该尊重每一位作者的付出， 请不要随意传播下载后的文件')


def get_detail(url, path, name):
    response = requests.get(url=url, headers=headers)
    selector = Selector(text=response.text)
    text_maker = ht.HTML2Text()
    create_time = selector.css(u'.time abbr::attr(title)').extract_first()
    print('文章时间为: ' + create_time)
    html = selector.css(u'.xzl-topic-body-content').extract_first()
    file_name = name
    if hasTime:
        file_name = create_time+' '+name
    if markdown:
        md = text_maker.handle(html)
        with open(path + file_name + '.md', 'w') as f:
            f.write(md)
    else:
        pdfkit.from_string(html, path + file_name + '.pdf')


if __name__ == '__main__':
    print('我们应该尊重每一位作者的付出， 请不要随意传播下载后的文件')
    # 专栏地址，仅填写最后一位即可，如：https://xiaozhuanlan.com/abc, 填写abc即可
    start('abc')