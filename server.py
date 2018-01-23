import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import os
import time
import hashlib
import json
import datetime
import pytz
from pymongo import MongoClient
from aliecs import AliECS
from tornado.options import define, options


define('port', default=8888, help='run on the given port', type=int)
with open('config.json') as fp:
    alibaba_cloud_config = json.loads(fp.read())

client = MongoClient('192.168.1.141', 27017)
db = client.colinshi

def md5(obj):
    m = hashlib.md5()   
    m.update(obj.encode('utf-8'))
    return m.hexdigest()

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        if self.get_secure_cookie('user'):
            return self.get_secure_cookie('user').decode('utf-8')
        else:
            return self.get_secure_cookie('user')

class LoginHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render('login.html')

    def post(self):
        account = self.get_argument('account')
        password = self.get_argument('password')        
        if account == "" or password == "":
            self.write('<h1>账号密码不能为空</h1><ui><a href="/login">返回</a></ui>')
            #self.redirect('/login')
        elif db.user.count({'account':account,'password':md5(password)}) > 0:
            self.write('{0}登入成功'.format(account))
            self.set_secure_cookie('user',account)
            self.redirect('/')
        else:
            self.write('<h1>账号或密码错误</h1><ui><a href="/login">返回</a></ui>')
            #self.redirect('/login')
    
class WelcomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        weibo = db.weibo.find({'account':{'$ne':self.get_current_user()}}).sort([("td",-1)])
        self.render('index.html',**{'user':self.current_user})

class LogoutHandler(BaseHandler): 
    def get(self):
        #if (self.get_argument('logout', None)):
        self.clear_cookie('user')
        self.redirect('/login')

class RegisterHandler(BaseHandler):
    def get(self):
        self.render('register.html')

    def post(self):
        account = self.get_argument('account')
        password = self.get_argument('password')
        email = self.get_argument('email')
        address = self.get_argument('address')
        bday = self.get_argument('bday')
        sex = self.get_argument('sex')
        if self.get_argument('registerID') != 'colinshifriend':
            print(self.get_argument('registerID'))
            self.write("仅接受邀请用户注册")
        elif account == "" or password == "":
            self.write("账号密码不能为空")
        elif db.user.count({'account':account}) > 0:
            self.write('账号已被注册，请更换用户名')
        else:
            db.user.insert({'account':account, 'password':md5(password), 'email':email, 'address':address,
                            'bday':bday, 'sex':sex})
            self.write('{0}账号注册成功'.format(account))
            self.set_secure_cookie('user',account)
            self.redirect('/')


class VPNHandler(BaseHandler):
    def post(self):
        self.CITY = self.get_argument('CITY')
        IMAGE_ID = self.get_argument('IMAGE_ID')
        INSTANCE_TYPE = self.get_argument('INSTANCE_TYPE')
        SECURITY_GROUP_ID = self.get_argument('SECURITY_GROUP_ID')
        Password = alibaba_cloud_config.get('password')
        InternetMaxOut = self.get_argument('InternetMaxOut')
        SpotStrategy = self.get_argument('SpotStrategy')
        Time  = self.get_argument('TIME')
        DateTime = time.strftime('%Y-%m-%d'+'T'+'%H'+':59'+':00'+'Z',time.localtime(time.time()-(3600*(8-int(Time)))))
        ecs_obj = AliECS(self.CITY, Time)
        InstanceStatus  = ecs_obj.Instances_status(self.CITY)
        if self.CITY not in alibaba_cloud_config.get('city'):
            self.render('alwaysvpn.html', **{'aaa':'世界服务器版本正在研发中，请赞助100元，开通美国服务器'})
        elif Time not in ('1','2','3','4'):
            self.render('alwaysvpn.html', **{'aaa':'请联系colinshi，给钱就给你开(每月收费20元)'})
        else:
            print(InstanceStatus.get('Instances').get('Instance'))
            if InstanceStatus.get('TotalCount') == 0:
                Instance_Id = ecs_obj.create_after_pay_instance(
                    IMAGE_ID, INSTANCE_TYPE, SECURITY_GROUP_ID,
                    InternetMaxOut, Password, SpotStrategy)
                ecs_status = InstanceStatus.get('Instances').get('Instance')
                while ecs_status == [] :
                    time.sleep(1)
                    InstanceStatus = ecs_obj.Instances_status(self.CITY)
                    ecs_status = InstanceStatus.get('Instances').get('Instance')
                while ecs_status[0].get('Status') not in ('Running', 'Stopped'):
                    time.sleep(1)
                    InstanceStatus = ecs_obj.Instances_status(self.CITY)
                    ecs_status = InstanceStatus.get('Instances').get('Instance')
                ecs_obj.Auto_Release_Time(Instance_Id, DateTime)
                ipaddress = ecs_obj.Add_Ip(Instance_Id)
                ecs_obj.Domain_Record('VPN','A',ipaddress.get('IpAddress'))
                ecs_obj.Start_Instance(Instance_Id)
                InstanceStatus  = ecs_obj.Instances_status(self.CITY)
            self.render('vpnlist.html',**{'InstanceStatus':InstanceStatus.get('Instances').get('Instance')})

    @tornado.web.authenticated
    def get(self):
        ecs_obj = AliECS()
        InstanceStatus = ecs_obj.Instances_status('cn-hongkong')
        if InstanceStatus.get('TotalCount') > 0:
            self.render('vpnlist.html',**{'InstanceStatus':InstanceStatus.get('Instances').get('Instance')})
        else:
             self.render('vpnlist.html',**{'InstanceStatus':None})




class TestHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        statuses  = RegionId_Status('cn-hongkong')
        if statuses.get('InstanceStatuses').get('InstanceStatus'):
            Instance_Id = statuses.get('InstanceStatuses').get('InstanceStatus')[0].get('InstanceId')
            instance_status = Instance_Status(Instance_Id)
        if instance_status.get('PublicIpAddress').get('IpAddress'):
            ipaddress = instance_status.get('PublicIpAddress').get('IpAddress')
        else:
            ipaddress = Add_Ip(Instance_Id).get('IpAddress')     
        DNSAdd = Domain_Record('vpn', 'A', ipaddress[0])
        recordid = Get_RecordId('colinshi.top')
        self.render('test.html',**{'DNSList':DNSAdd,'ipaddress':recordid})
        


if __name__== "__main__":
    tornado.options.parse_command_line()

    settings = {"cookie_secret": "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
                'xsrf_cookies' : True,
                'template_path': os.path.join(os.path.dirname(__file__),'templates'),
                'static_path': os.path.join(os.path.dirname(__file__),'statics'),
                'static_url_prefix':'/statics/',
                'login_url': '/login',
                'debug': True}

    url = [(r'/', WelcomeHandler),
           (r'/register', RegisterHandler),
           (r'/login',LoginHandler),
           (r'/logout',LogoutHandler),
           (r'/vpnadd',VPNHandler),
           (r'/vpnlist',VPNHandler),
           (r'/test',TestHandler),
            ]
    application = tornado.web.Application(url, **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()