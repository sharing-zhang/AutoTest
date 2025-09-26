from rest_framework.decorators import api_view
from myapp import utils
from myapp.handler import APIResponse
from myapp.models import User
from myapp.serializers import UserSerializer
from myapp.utils import md5value


@api_view(['POST'])
def user_login(request):
    """普通用户登录"""
    username = request.data['username']
    password = utils.md5value(request.data['password'])

    # 查找普通用户（角色为'2'）
    users = User.objects.filter(username=username, password=password, role='2', status='0')
    if len(users) > 0:
        user = users[0]
        data = {
            'username': username,
            'password': password,
            'token': md5value(username)  # 生成普通用户token
        }
        serializer = UserSerializer(user, data=data)
        if serializer.is_valid():
            serializer.save()
            return APIResponse(code=0, msg='登录成功', data=serializer.data)
        else:
            print(serializer.errors)

    return APIResponse(code=1, msg='用户名或密码错误')


@api_view(['POST'])
def user_register(request):
    """普通用户注册"""
    if not request.data.get('username', None) or not request.data.get('password', None):
        return APIResponse(code=1, msg='用户名或密码不能为空')
    
    users = User.objects.filter(username=request.data['username'])
    if len(users) > 0:
        return APIResponse(code=1, msg='该用户名已存在')

    data = request.data.copy()
    data.update({
        'password': utils.md5value(request.data['password']),
        'role': '2',  # 设置为普通用户
        'status': '0'  # 设置为正常状态
    })
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='注册成功', data=serializer.data)
    else:
        print(serializer.errors)

    return APIResponse(code=1, msg='注册失败')
