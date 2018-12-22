import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
 
import requests
import time
import random
from bs4 import BeautifulSoup

def google_scrape(keywords):
    title_list=[]
    base='https://www.google.com.tw/search?q={}&rlz=1C5CHFA_enTW810TW810&tbm=nws&source=lnt&tbs=qdr:d&sa=X&ved=0ahUKEwihzbbY2ofeAhXIvrwKHaN7Ap8QpwUIHA&biw=1440&bih=803&dpr=2'
    url = base.format(keywords.replace(' ', '+'))
    user_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0', \
          'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0', \
          'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533+ \
          (KHTML, like Gecko) Element Browser 5.0', \
          'IBM WebExplorer /v0.94', 'Galaxy/1.0 [en] (Mac OS X 10.5.6; U; en)', \
          'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)', \
          'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14', \
          'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) \
           Version/6.0 Mobile/10A5355d Safari/8536.25', \
          'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) \
           Chrome/28.0.1468.0 Safari/537.36', \
          'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; TheWorld)']   
#     proxies = {
#       "http": "http://113.200.214.164:9999"}
    index = random.randint(0, 9)
    user_agent = user_agents[index]
    res=requests.get(url,user_agent)
    soup=BeautifulSoup(res.text, "html.parser")
    res = {result.find("a").text:result.find("a")['href'][7:].split('&sa')[0] for result in soup.find_all("div", class_="g")}
    def email_str(d):
        gen = iter(d.items())
        contents = '{} News - {}\n\n'.format(time.strftime("%Y-%m-%d", time.localtime()), keywords)
        while True:
            try:
                one = next(gen)
                contents += '{}  |  {} {}'.format(one[0], one[1], '\n\n')
            except StopIteration:
                print('StopIteration')
                break
        return contents
    res = email_str(res)
    return res

my_sender = 'gary.li@tixguru.co'    # 发件人邮箱账号
my_pass = 'a1234567'              # 发件人邮箱密码
# my_receiver = 'sarcas0705@gmail.com'    # 收件人邮箱账号

def mail(words, recipients):
    ret=(words, 1)
    try:
        msg=MIMEText(google_scrape(words),'plain','utf-8')
        msg['From']=formataddr(["Gary Li",my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To']=",".join(recipients)             # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject']=words                # 邮件的主题，也可以说是标题
 
        server=smtplib.SMTP_SSL('smtp.gmail.com', 465)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender,recipients,msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception as e:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        print('Exception: ', e)
        ret=(words, 0)
    return ret

if __name__ == '__main__':
#     while True:
    topic = ['security token offering real estate']
#     'crypto regulation swiss', 'stablecoin', 'crypto bank swiss'
    to_list = ['farrah@tixguru.co', 'yc@tixguru.co', 'Cathy@tixguru.co', 'santai@tixguru.co', 'jemmy.lai@tixguru.co', 'pete@tixguru.co', 'russel@tixguru.co']
    mail_result=[]
    for i in topic:
        t = mail(i, to_list)
        mail_result.append(t)
    print("{} @ {}".format(str(mail_result) ,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))