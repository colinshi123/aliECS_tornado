import json
import datetime
import pytz
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import RpcRequest
from aliyunsdkecs.request.v20140526.CreateInstanceRequest import CreateInstanceRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.StartInstanceRequest import StartInstanceRequest
from aliyunsdkecs.request.v20140526.StopInstanceRequest import StopInstanceRequest
from aliyunsdkecs.request.v20140526.ModifyInstanceAutoReleaseTimeRequest import ModifyInstanceAutoReleaseTimeRequest
from aliyunsdkecs.request.v20140526.AllocatePublicIpAddressRequest import AllocatePublicIpAddressRequest
from aliyunsdkecs.request.v20140526.DescribeInstanceStatusRequest import DescribeInstanceStatusRequest
from aliyunsdkecs.request.v20140526.DescribeInstanceAttributeRequest import DescribeInstanceAttributeRequest





class AliECS(object):
    def __init__(self, city = 'cn-hongkong', time = 2):
        self.city = city
        self.time = 2


    #创建ecs实例
    def create_after_pay_instance(self, image_id, instance_type, security_group_id, internetmaxbandwidthout, password, spotstrategy):
        request = CreateInstanceRequest();
        request.add_query_param('InternetMaxBandwidthOut', 100)
        request.add_query_param('InternetChargeType', 'PayByTraffic')
        request.add_query_param('ImageId', image_id)
        request.add_query_param('SecurityGroupId', security_group_id)
        request.add_query_param('InstanceType', instance_type)
        request.add_query_param('Password', password)
        request.add_query_param('SpotStrategy', spotstrategy)
        response = self._send_request(request)
        instance_id = response.get('InstanceId')
        '''
        #logging.info("instance %s created task submit successfully.", instance_id)
        req = StartInstanceRequest()
        req.set_InstanceId(instance_id)
        self._send_request(req)
        '''
        return instance_id

    #启动实例
    def Start_Instance(self, instance_id):
        request = StartInstanceRequest()
        request.set_InstanceId(instance_id)
        self._send_request(request)
    #停止实例
    def Stop_Instance(self, instance_id):
        request = StopInstanceRequest()
        request.set_InstanceId(instance_id)
        self._send_request(request)

    #实例状态
    def Instances_status(self, RegionId):
        request = DescribeInstancesRequest()
        request.set_accept_format('json')
        request.add_query_param('RegionId', RegionId)
        response = self._send_request(request)
        if response.get('TotalCount') == 0:
            return response
        else:
            for i in range(response.get('TotalCount')):
                response['Instances']['Instance'][i]['AutoReleaseTime'] = self.utc_to_local(response.get('Instances').get('Instance')[i].get('AutoReleaseTime'))
            return response

    def Add_Ip(self, instance_id):
        request = AllocatePublicIpAddressRequest()
        request.set_accept_format('json')
        request.add_query_param('InstanceId',instance_id)
        response = self._send_request(request)
        #logging.info("instance %s created task submit successfully.", instance_id)
        return response


    def Auto_Release_Time(self, instance_id, time):
        # 设置参数
        request = ModifyInstanceAutoReleaseTimeRequest()
        #设置JSON格式
        request.set_accept_format('json')
        #设置实例ID
        request.add_query_param('InstanceId', instance_id)
        #设置释放实例时间
        request.add_query_param('AutoReleaseTime', time)
        # 发起请求
        response = self._send_request(request)
        # 输出结果
        return response

    #指定区域下的实例信息
    def RegionId_Status(self, RegionId):
        # 设置参数
        request = DescribeInstanceStatusRequest()
        #设置JSON格式
        request.set_accept_format('json')
        #设置实例地域
        request.add_query_param('RegionId', RegionId)
        # 发起请求
        response = self._send_request(request)
        # 输出结果
        return response

    #请求实例状态
    def Instance_Status(self, instance_id):
        # 设置参数
        request = DescribeInstanceAttributeRequest()
        #设置JSON格式
        request.set_accept_format('json')
        #设置实例
        request.add_query_param('InstanceId', instance_id)
        # 发起请求
        response = self._send_request(request)
        # 输出结果
        return response

    def Get_RecordId(self, DomainName):
        request=RpcRequest('Alidns', '2015-01-09', 'DescribeDomainRecords')
        request.add_query_param("DomainName",DomainName)
        response=self._send_request(request)
        return response

    def Domain_Record(self, RR,Type,Value):
        request=RpcRequest('Alidns', '2015-01-09', 'UpdateDomainRecord')
        request.add_query_param("RecordId",'3645564013972480')
        request.add_query_param("RR",RR)
        request.add_query_param("Type",Type)
        request.add_query_param("Value",Value)
        request.set_accept_format('json')
        response=self._send_request(request)
        return response

    # UTCS时间转换为时间戳 2016-07-31T16:00:00Z
    def utc_to_local(self, utc_time_str, utc_format='%Y-%m-%dT%H:%MZ'):
        if utc_time_str:
            local_tz = pytz.timezone('Asia/Shanghai')
            local_format = "%Y-%m-%d %H:%M"
            utc_dt = datetime.datetime.strptime(utc_time_str, utc_format)
            local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
            time_str = local_dt.strftime(local_format)
            return time.strftime("%Y-%m-%d %H:%M",time.localtime(int(time.mktime(time.strptime(time_str, local_format)))))
        else:
            return
    # 发送API请求
    def _send_request(self, request):
        request.set_accept_format('json')
        with open('config.json') as fp:
            alibaba_cloud_config = json.loads(fp.read())
            acs  = AcsClient(alibaba_cloud_config.get('AccessKeyID'), 
                         alibaba_cloud_config.get('AccessKeySecret'), 'cn-hongkong')
        try:
            response_str = acs.do_action_with_exception(request)
            #logging.info(response_str)
            response_detail = json.loads(response_str)
            return response_detail
        except Exception as e:
            return e