from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from myapp.models import User


# 接口认证
class AdminTokenAuthtication(BaseAuthentication):
    def authenticate(self, request):
        adminToken = request.META.get("HTTP_ADMINTOKEN")
        print(f"检查adminToken==>{adminToken}")
        print(f"请求头: {dict(request.META)}")

        users = User.objects.filter(admin_token=adminToken)
        print(f"找到用户数量: {len(users)}")
        if users:
            print(f"用户信息: ID={users[0].id}, Username={users[0].username}, Role={users[0].role}")
        
        """
        判定条件：
            1. 传了adminToken
            2. 查到了该帐号
            3. 该帐号是管理员或演示帐号
        """
        if not adminToken or len(users) == 0 or users[0].role == '2':
            print(f"认证失败: adminToken={adminToken}, users_count={len(users)}")
            if users:
                print(f"用户角色: {users[0].role}")
            raise exceptions.AuthenticationFailed("AUTH_FAIL_END")
        else:
            print('adminToken验证通过')
            return (users[0], None)  # 返回用户对象和token


# 普通用户认证
class UserTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        userToken = request.META.get("HTTP_TOKEN")
        print(f"检查userToken==>{userToken}")

        users = User.objects.filter(token=userToken)
        print(f"找到用户数量: {len(users)}")
        if users:
            print(f"用户信息: ID={users[0].id}, Username={users[0].username}, Role={users[0].role}")
        
        """
        判定条件：
            1. 传了userToken
            2. 查到了该帐号
            3. 该帐号是普通用户
        """
        if not userToken or len(users) == 0 or users[0].role != '2':
            print(f"认证失败: userToken={userToken}, users_count={len(users)}")
            if users:
                print(f"用户角色: {users[0].role}")
            raise exceptions.AuthenticationFailed("USER_AUTH_FAIL_END")
        else:
            print('userToken验证通过')
            return (users[0], None)  # 返回用户对象和token



