# -*- coding:utf-8 -*-
import os
import sys
import time
from qq import qq
from util import util
import urllib.request
from selenium import webdriver
import subprocess

# 浏览器驱动程序路径
if util.detect_os() == 'windows':
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    filename = 'login\phantomjs.exe'
    driver_file = path + os.sep + filename
elif util.detect_os() == 'linux':
    driver_file = 'phantomjs'


class Login(object):
    """
    qq 登录模块
    """
    def __init__(self, user, pwd):
        self.qq = qq.QQ(user, pwd)
        self.cookies = None

    def login(self):
        """使用 selenium 模拟登录"""
        # driver = webdriver.Chrome('chromedriver_path')
        driver = webdriver.PhantomJS(driver_file)         # 驱动的路径

        driver.get('http://i.qq.com/')
        driver.switch_to_frame('login_frame')
        driver.find_element_by_id('switcher_plogin').click()

        driver.find_element_by_name('u').clear()
        driver.find_element_by_name('u').send_keys(self.qq.user)
        driver.find_element_by_name('p').clear()
        driver.find_element_by_name('p').send_keys(self.qq.pwd)

        driver.execute_script("document.getElementById('login_button').parentNode.hidefocus=false;")
        driver.find_element_by_xpath('//*[@id="loginform"]/div[4]/a').click()
        driver.find_element_by_id('login_button').click()
        time.sleep(2)

        if driver.current_url != ('https://user.qzone.qq.com/' + self.qq.user):
            print('trying get captcha...')
            driver.switch_to_frame(driver.find_element_by_tag_name("iframe"))
            captcha_src = driver.execute_script("return document.getElementsByTagName('img')['capImg'].src")
            urllib.request.urlretrieve(captcha_src, "captcha.jpg")
            print('captcha saved in ./captcha.jpg')

            if util.detect_os() == 'windows':
                os.startfile("captcha.jpg")
            elif util.detect_os() == 'linux':
                subprocess.call(["xdg-open", "captcha.jpg"])

            captcha = input("please input captcha: ")
            driver.find_element_by_id('capAns').clear()
            driver.find_element_by_id('capAns').send_keys(captcha)

            driver.find_element_by_id('submit').click()

            time.sleep(2)
            if driver.current_url != ('https://user.qzone.qq.com/' + self.qq.user):
                print('incorrect verification code, please try again.')

        driver.get('https://user.qzone.qq.com/' + self.qq.user)
        self.cookies = driver.get_cookies()             # 获取 cookie

        if len(self.cookies) < 10:
            print('username or password was wrong, please try again.')
            sys.exit(0)

    def check_login(self, qq, cookie):
        """
        测试登录模块，尝试获取登录成功后才能访问的页面内容，以此判断是否登录成功
        """
        s = qq.session

        # 别的 qq 的 cookie 或者无效 cookie
        if 'uin' in cookie and qq.user in cookie.get('ptui_loginuin'):
            s.cookies = cookie
        else:
            print('cookies was unavailable, please delete the cookies file and try again.')
            return False

        g_tk = str(self.qq.g_tk())

        url = 'https://h5.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/user/cgi_personal_card?uin=' + qq.user + '&g_tk=' + g_tk
        header = util.headers
        r = s.get(url, headers=header)
        if r.content.decode().find('登录') > 0:
            print('cookies was expired or unavailable, please delete the cookies file and try again.')
            return False
        else:
            print('login success.')
            try:
                print('Hi, ' + eval(r.content[10:-3]).get('nickname') + '\n')
            except:
                print('sorry, name cannot display')    # 有些奇怪的昵称无法在终端显示，比如含有 emoji 的昵称
            return True

    def login_test(self):
        """
        登录入口，判断是第一次登录还是从 cookie 登录
        """
        s = self.qq.session
        cookie_file = util.cookie_file

        if util.cookie is None:
            print('login...\nplease wait...')
            self.login()
            for item in self.cookies:
                s.cookies.set(item['name'], item['value'])
            util.save_cookie_to_file(self.cookies, cookie_file)             # 保存 cookie 到文件
            cookies = s.cookies
        else:
            print('trying login by cookies...')
            cookies = util.get_cookie()                                     # 从文件读取 cookie

        return self.check_login(self.qq, cookies)
