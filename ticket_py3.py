# _*_ coding: utf-8 _*_
from selenium import webdriver
import requests
from bs4 import BeautifulSoup
import threading
import random
from urllib.parse import urljoin
import traceback
import json
import time

class Ticket(object):
    def __init__(self, username, password, seattype, brand_id):
        self.username = username
        self.password = password
        self.seattype = seattype
        self.brand_id = brand_id
        self.cookies = {}
        self.items = []

    def query(self, url, headers, proxies=None):
        r = requests.get(url, headers=headers, proxies=proxies, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        i = 0
        for item_class in soup.find_all(class_="gs_2t"):
            data = {}
            item = item_class.find('a')
            data['title'] = str(i) + ' ' + item.get('title')
            data['href'] = item.get('href')
            self.items.append(data)
            i += 1
            print(data['title'])
        print(self.items)

    def login(self, url_login):
        #设置代理
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=http://127.0.0.1:8888')

        browser = webdriver.Chrome('chromedriver.exe', chrome_options=chrome_options)
        browser.maximize_window()
        # 隐式等待10s
        browser.implicitly_wait(10)
        # 设定页面加载限制时间
        browser.set_page_load_timeout(30)
        browser.get(url_login)
        browser.find_element_by_id('login').click()
        browser.find_element_by_id('username').send_keys(self.username)
        browser.find_element_by_id('password').send_keys(self.password)
        browser.find_element_by_id('submit').click()
        #等待页面跳转
        time.sleep(5)
        # #刷新页面
        # browser.refresh()
        browser.find_element_by_link_text('SNH48 GROUP官方商城').click()
        browser.switch_to_window(browser.window_handles[-1])
        tmp = browser.get_cookies()
        print(tmp)
        # for i in browser.get_cookies():
        #     self.cookies += i['name']
        #     self.cookies += '='
        #     self.cookies += i['value']
        #     self.cookies +=';'
        # self.cookies.strip(';')
        for i in browser.get_cookies():
            self.cookies[i['name']] = i['value']
        print(self.cookies)
        browser.quit()

    def order(self, url_shop, id, headers, proxies=None):
        #session只能保持cookiejar格式的cookie，dict格式的不行
        cookies = requests.utils.cookiejar_from_dict(self.cookies, cookiejar=None, overwrite=True)
        session = requests.session()
        session.cookies = cookies
        #验证cookie是否能登陆
        res = session.get('https://shop.48.cn/Account', proxies=proxies, verify=False)
        print(res.url)
        #get访问购买页面
        url_item = urljoin(url_shop, self.items[id]['href'])
        res = session.get(url_item, proxies=proxies, verify=False)

        ticketcode = self.items[id]['href'].split('/')[-1]
        postData = {'id':ticketcode, 'num':'1', 'seattype':self.seattype,
                    'brand_id':self.brand_id, 'r':'%.17f' %random.random(), 'choose_times_end':'-1'}
        payload = {'id':ticketcode, 'brand_id':self.brand_id}
        url_amount = urljoin(url_shop, 'tickets/saleList')
        type = int(self.seattype) - 1
        while 1:
            try:
                res = session.get(url_amount, params=payload)
            except:
                traceback.print_exc()
                continue
            #res.content类型为bytes, .decode('utf-8')之后为str
            if json.loads(res.content.decode('utf-8'))[type]['amount']:
                url_order = urljoin(url_shop, 'TOrder/add')
                resp = session.post(url_order, data=postData, proxies=proxies, verify=False)
                if resp.status_code == 200:
                    print(resp.text)
                    print('order sucess!')
                    break
                else:
                    print('order defeat!')
            else:
                print('no amount!')
            time.sleep(1)


if __name__ == '__main__':
    #48票务页面
    url_ticket = 'https://shop.48.cn/tickets?brand_id=3'
    url_login = 'http://vip.48.cn/Home/Login/index.html'
    url_shop = 'https://shop.48.cn'

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
    headers = {'User-Agent': user_agent}
    #调试代理--fiddle
    proxies = {'http': 'http://127.0.0.1:8888'}

    username = 'username'
    password = 'password'
    #门票类型 2，3普，4站
    seattype = '3'
    brand_id = url_ticket.split('=')[-1]
    ticket = Ticket(username, password, seattype, brand_id)
    ticket.query(url_ticket, headers, proxies)
    ids = input('请选择购买序号：as: 0,1')
    if ids is not None:
        ticket.login(url_login)
        ids = ids.split(',')  # str字符串
        for id in ids:
            id = int(id)
            th = threading.Thread(target=ticket.order, args=(url_shop, id, headers, proxies))
            th.start()