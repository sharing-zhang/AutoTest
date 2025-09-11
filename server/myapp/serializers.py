from rest_framework import serializers

from myapp.models import ScanDevUpdate_scanResult, ScanUpdate, Thing, User, LoginLog, OpLog, \
    ErrorLog, Plugin, Script, TaskExecution, PageScriptConfig


# serializers作用可以用来规定提交数据后返回的数据字段，这里就返回时间即可
class ScanDevUpdate_scanResult_Serializer(serializers.ModelSerializer):
    # format可以设置时间的格式，下面例子会输出如:2018-1-24 12:10:30
    # required=False 设置非必填项
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = ScanDevUpdate_scanResult
        fields = '__all__'

class UpdateScanDevUpdate_scanResult_SerializerSerializer(serializers.ModelSerializer):

    class Meta:
        model = ScanDevUpdate_scanResult
        # 排除多对多字段
        exclude = ()


# serializers作用可以用来规定提交数据后返回的数据字段，这里就返回时间即可
class ScanUpdateSerializer(serializers.ModelSerializer):
    # format可以设置时间的格式，下面例子会输出如:2018-1-24 12:10:30
    # required=False 设置非必填项
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = ScanUpdate
        fields = '__all__'

class UpdateScanUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = ScanUpdate
        # 排除多对多字段
        exclude = ()

class ThingSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = Thing
        fields = '__all__'


class DetailThingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Thing
        # 排除多对多字段
        exclude = ('wish', 'collect',)


class UpdateThingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Thing
        # 排除多对多字段
        exclude = ()


class ListThingSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = Thing
        # 排除字段
        exclude = ('wish', 'collect', 'description',)


class UserSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = User
        fields = '__all__'
        # exclude = ('password',)

class PluginSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = Plugin
        fields = '__all__'


class LoginLogSerializer(serializers.ModelSerializer):
    log_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = LoginLog
        fields = '__all__'


class OpLogSerializer(serializers.ModelSerializer):
    re_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = OpLog
        fields = '__all__'


class ErrorLogSerializer(serializers.ModelSerializer):
    log_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = ErrorLog
        fields = '__all__'



class ScriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Script
        fields = '__all__'

class TaskExecutionSerializer(serializers.ModelSerializer):
    script_name = serializers.CharField(source='script.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TaskExecution
        fields = '__all__'

class PageScriptConfigSerializer(serializers.ModelSerializer):
    script = ScriptSerializer(read_only=True)
    
    class Meta:
        model = PageScriptConfig
        fields = '__all__'