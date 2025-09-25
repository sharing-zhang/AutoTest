# http://172.16.34.33:8001/admin/scanUpdate 链接下展示资源扫描各项目详细信息页面的服务器端代码
# 记得在views/admin/__init__.py也加上新增的路由
from pyexpat.errors import messages
from rest_framework.decorators import api_view, authentication_classes

from myapp import utils
from myapp.auth.authentication import AdminTokenAuthtication
from myapp.handler import APIResponse
from myapp.models import ScanDevUpdate_scanResult
from myapp.permission.permission import isDemoAdminUser
from myapp.serializers import ScanDevUpdate_scanResult_Serializer, UpdateScanDevUpdate_scanResult_SerializerSerializer
from dingtalkchatbot.chatbot import DingtalkChatbot, ActionCard, FeedLink, CardItem
import pandas as pd

@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        # keyword是当有搜索栏对应搜索内容时使用，没有搜索内容则为空
        keyword = request.GET.get("keyword", None)
        if keyword:
            scanupdates_scanresult = ScanDevUpdate_scanResult.objects.filter(scandevresult_filename__contains=keyword).order_by('-scandevresult_time')
        else:
            scanupdates_scanresult = ScanDevUpdate_scanResult.objects.all().order_by('-scandevresult_time')
        # serializer: 将服务端的数据结构（如模型类对象）转换为客户端可接受的格式（如字典、JSON），
        # 同时也能将客户端的数据（如JSON）转换为服务端的数据结构。这种转换过程包括序列化（将数据转换为可传输的格式）和反序列化（将传输格式的数据还原为Python数据类型）
        serializer = ScanDevUpdate_scanResult_Serializer(scanupdates_scanresult, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['GET'])
def detail(request):

    try:
        pk = request.GET.get('id', -1)
        scanupdates_scanresult = ScanDevUpdate_scanResult.objects.get(pk=pk)
    except ScanDevUpdate_scanResult.DoesNotExist:
        utils.log_error(request, '对象不存在')
        return APIResponse(code=1, msg='对象不存在')

    if request.method == 'GET':
        serializer = ScanDevUpdate_scanResult_Serializer(scanupdates_scanresult)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request):

    if isDemoAdminUser(request):
        return APIResponse(code=1, msg='演示帐号无法操作')

    serializer = ScanDevUpdate_scanResult_Serializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        print(serializer.errors)
        utils.log_error(request, '参数错误')

    return APIResponse(code=1, msg='创建失败')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):

    # 判断是否是演示账号，用于账号隔离
    if isDemoAdminUser(request):
        return APIResponse(code=1, msg='演示帐号无法操作')

    try:
        # 在数据库中能否搜索到对应id，没有的话则为-1
        # pk‌：代表主键（Primary Key），是每个模型的主键字段。在大多数情况下，主键字段名为id
        pk = request.GET.get('id', -1)
        # scanupdates_scanresult代表数据库中通过id关键字搜索到数据库内容，不是json类型
        scanupdates_scanresult = ScanDevUpdate_scanResult.objects.get(pk=pk)

    except ScanDevUpdate_scanResult.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')
    # request.data代表玩家请求体传参的内容
    # scanupdates_scanresult代表数据库中通过id关键字搜索到数据库内容
    # serializer序列化后，将数据库返回的内容转化为json格式
    serializer = UpdateScanDevUpdate_scanResult_SerializerSerializer(scanupdates_scanresult, data=request.data)

    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='项目信息更新成功', data=serializer.data)
    else:
        print(serializer.errors)
        utils.log_error(request, '参数错误')

    return APIResponse(code=1, msg='项目信息更新失败')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):

    if isDemoAdminUser(request):
        return APIResponse(code=1, msg='演示帐号无法操作')

    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        ScanDevUpdate_scanResult.objects.filter(id__in=ids_arr).delete()
    except ScanDevUpdate_scanResult.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')
    return APIResponse(code=0, msg='删除成功')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def sendmessage(request):
    # 判断是否是演示账号，用于账号隔离
    if isDemoAdminUser(request):
        return APIResponse(code=1, msg='演示帐号无法操作')

    try:
        # 在数据库中能否搜索到对应id，没有的话则为-1
        # pk‌：代表主键（Primary Key），是每个模型的主键字段。在大多数情况下，主键字段名为id
        pk = request.GET.get('id', -1)
        scanupdates_scanresult = ScanDevUpdate_scanResult.objects.get(pk=pk)

    except ScanDevUpdate_scanResult.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在',data=request.data)

    try:
        # 获取通过id查询到的数据库内容，并且转化为json可读格式
        serializer = ScanDevUpdate_scanResult_Serializer(scanupdates_scanresult)

        # 新版的钉钉自定义机器人必须配置安全设置（自定义关键字、加签、IP地址/段），其中“加签”需要传入密钥才能发送成功
        webhook = request.data.get('resultSendDingDingRobot_webhook')
        secret = request.data.get('resultSendDingDingRobot_secret')

        # 初始化机器人
        # 新版安全设置为“加签”时，需要传入请求密钥
        # 同时支持设置消息链接跳转方式，默认pc_slide=False为跳转到浏览器，pc_slide为在PC端侧边栏打开
        # 同时支持设置消息发送失败时提醒，默认fail_notice为false不提醒，开发者可以根据返回的消息发送结果自行判断和处理
        robotxiaoding = DingtalkChatbot(webhook, secret, pc_slide=True, fail_notice=False)
        scanResult_text = ("执行脚本： " + serializer.data.get('scandevresult_filename') + "\n执行时间： "
                           + pd.to_datetime(serializer.data.get('scandevresult_time')).strftime("%Y-%m-%d %H.%M.%S")
                           + "\n执行结果： " + serializer.data.get('script_output'))
        # text 控制钉钉自定义机器人中发送消息
        robotxiaoding.send_text(msg=scanResult_text, is_at_all=False)
        return APIResponse(code=0, msg='钉钉机器人信息已成功发送，请进对应群中检查；如果未收到消息，请检查webhook与密钥是否正确', data=serializer.data)
    except Exception as e:
        print(e)
        return APIResponse(code=1, msg='消息发送失败，请检查webhook与密钥是否正确',data=request.data)