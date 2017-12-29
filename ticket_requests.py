# _*_ coding: utf-8 _*_
import requests
from bs4 import BeautifulSoup
import threading
import random
from urllib.parse import urljoin
import traceback
import json
import time
from datetime import datetime

class Ticket(object):
    def __init__(self, start_time, seattype, brand_id, cookies):
        self.start_time = start_time
        self.seattype = seattype
        self.brand_id = brand_id
        self.cookies = cookies
        self.items = []
        self.session = requests.session()

    def query(self, url, headers, proxies=None):
        # r = requests.get(url, headers=headers, proxies=proxies, verify=False)
        r = requests.get(url, headers=headers, proxies=proxies)
        soup = BeautifulSoup(r.text, 'html.parser')
        i = 0
        for item_class in soup.find_all(class_="gs_2t"):
            data = {}
            item = item_class.find('a')
            title = item.text
            if title.find('星梦剧院') == -1:  # or if '星梦剧院' in title
                continue
            data['title'] = str(i) + ' ' + title
            data['href'] = item.get('href')
            self.items.append(data)
            i += 1
            print(data['title'])
        print(self.items)

    def waiting(self, start_time):
        youtime = 1
        rm_secends = 60
        while (youtime > 0):
            rm_secends_last = rm_secends
            now = int(datetime.now().timestamp() * 1000) #ms
            start = start_time * 1000        #ms
            youtime = start - now
            secends = int(youtime / 1000)
            minutes = int(secends / 60)
            hours = int(minutes / 60)
            days = int(hours / 24)
            rm_days = days
            rm_hours = hours % 24
            rm_minutes = minutes % 60
            rm_secends = secends % 60

            if (rm_secends != rm_secends_last and rm_secends_last != 60):
                print(str(rm_hours) + '时' + str(rm_minutes) + '分' + str(rm_secends) + '秒 开售')

    def fighting(self, postData):
        #发送一次
        url_order = urljoin(url_shop, 'TOrder/add')
        res = self.session.post(url_order, data=postData, proxies=proxies)
        if res.status_code == 200:
            print(res.text)
        else:
            print('order defeat!')

    def ragman(self, id, postData):
        payload = {'brand_id': self.brand_id, 'team_type': '-1', 'date_type': '0'}
        url_amount = urljoin(url_shop, 'Home/IndexTickets')
        type = int(self.seattype) - 1
        while 1:
            try:
                res = self.session.get(url_amount, params=payload)
            except:
                traceback.print_exc()
                continue
            # res.content类型为bytes, .decode('utf-8')之后为str
            index_tickets = json.loads(res.content.decode('utf-8'))
            if index_tickets[id]['tickets_sales'][type]['amount']:
                url_order = urljoin(url_shop, 'TOrder/add')
                resp = self.session.post(url_order, data=postData, proxies=proxies)
                if resp.status_code == 200:
                    print(resp.text)
                    print('order sucess!')
                    break
                else:
                    print('order defeat!')
            else:
                print('no amount!')
            time.sleep(1)

    def order(self, url_shop, id, headers, proxies=None):
        #session只能保持cookiejar格式的cookie，dict格式的不行
        cookies = requests.utils.cookiejar_from_dict(self.cookies, cookiejar=None, overwrite=True)
        self.session.cookies = cookies
        #验证cookie是否能登陆
        res = self.session.get('https://shop.48.cn/Account', proxies=proxies)
        print(res.url)
        #get访问购买页面
        url_item = urljoin(url_shop, self.items[id]['href'])
        res = self.session.get(url_item, proxies=proxies, verify=False)

        ticketcode = self.items[id]['href'].split('/')[-1]
        postData = {'id':ticketcode, 'num':'1', 'seattype':self.seattype,
                    'brand_id':self.brand_id, 'r':'%.17f' %random.random(), 'choose_times_end':'-1'}

        #等待放票
        self.waiting(self.start_time)
        #抢票
        # self.fighting(postData=postData)
        #等待捡票
        self.waiting(self.start_time + 1200)
        #开始捡票
        self.ragman(id=id, postData=postData)

if __name__ == '__main__':
    #48票务页面
    url_ticket = 'https://shop.48.cn/tickets?brand_id=2'
    url_login = 'http://vip.48.cn/Home/Login/index.html'
    url_shop = 'https://shop.48.cn'
    start_time = '2017-12-26 20:00:00'
    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timestamp()

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
    headers = {'User-Agent': user_agent}
    #调试代理--fiddle
    proxies = {'http': 'http://127.0.0.1:8888'}
    #cookies
    with open('cookies.txt') as f:
        cookies_list = f.read().strip()
    cookies = dict([l.split('=') for l in cookies_list.split('; ')])

    #门票类型 2，3普，4站
    seattype = '3'
    brand_id = url_ticket.split('=')[-1]
    ticket = Ticket(start_time, seattype, brand_id, cookies)
    ticket.query(url_ticket, headers, proxies)
    ids = input('请选择购买序号：as: 0,1')
    if ids is not None:
        ids = ids.split(',')  # str字符串
        for id in ids:
            id = int(id)
            th = threading.Thread(target=ticket.order, args=(url_shop, id, headers))
            th.start()