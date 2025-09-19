# Create your views here.
from rest_framework.decorators import api_view, authentication_classes
from django.http import FileResponse, HttpResponseNotFound
from django.conf import settings
from django.utils.encoding import escape_uri_path
import os
import time

from myapp.auth.authentication import AdminTokenAuthtication
from myapp.handler import APIResponse
from myapp.models import Plugin
from myapp.permission.permission import isDemoAdminUser
from myapp.serializers import PluginSerializer


@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        plugins = Plugin.objects.all().order_by('-create_time')
        serializer = PluginSerializer(plugins, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request):
    if isDemoAdminUser(request):
        return APIResponse(code=1, msg='演示帐号无法操作')

    serializer = PluginSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)

    return APIResponse(code=1, msg='创建失败')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    if isDemoAdminUser(request):
        return APIResponse(code=1, msg='演示帐号无法操作')

    try:
        pk = request.GET.get('id', -1)
        plugin = Plugin.objects.get(pk=pk)
    except Plugin.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')

    serializer = PluginSerializer(plugin, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    else:
        print(serializer.errors)

    return APIResponse(code=1, msg='更新失败')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    if isDemoAdminUser(request):
        return APIResponse(code=1, msg='演示帐号无法操作')

    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Plugin.objects.filter(id__in=ids_arr).delete()
    except Plugin.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')

    return APIResponse(code=0, msg='删除成功')


# ============ 插件文件上传/下载 ============

PLUGIN_DIR = os.path.join(settings.MEDIA_ROOT, 'plugins')


def _ensure_plugin_dir():
    try:
        os.makedirs(PLUGIN_DIR, exist_ok=True)
    except Exception:
        pass


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def upload_exe(request):
    if isDemoAdminUser(request):
        return APIResponse(code=1, msg='演示帐号无法操作')

    #file_obj = request.FILES.get('file') or request.FILES.get('exe')
    file_obj = request.FILES.get('file')
    if not file_obj:
        return APIResponse(code=1, msg='未接收到文件')

    original_name = file_obj.name
    # ext = os.path.splitext(original_name)[1].lower()
    # if ext != '.exe':
    #     return APIResponse(code=1, msg='只允许上传 .exe 文件')

    _ensure_plugin_dir()
    safe_name = f"{int(time.time())}_{original_name}"
    save_path = os.path.join(PLUGIN_DIR, safe_name)

    with open(save_path, 'wb') as f:
        for chunk in file_obj.chunks():
            f.write(chunk)

    rel_path = os.path.join('plugins', safe_name).replace('\\', '/')
    desc = request.POST.get('description') or request.POST.get('desc') or ''
    display_name = request.POST.get('display_name') or request.POST.get('name') or original_name
    if desc:
        try:
            with open(save_path + '.meta.json', 'w', encoding='utf-8') as mf:
                import json as _json
                _json.dump({"description": desc, "display_name": display_name}, mf, ensure_ascii=False)
        except Exception:
            pass

    return APIResponse(code=0, msg='上传成功', data={
        'file_name': original_name,
        'stored_name': safe_name,
        'download_url': settings.MEDIA_URL + rel_path,
        'description': desc,
        'display_name': display_name
    })


@api_view(['GET'])
def list_exe(request):
    try:
        _ensure_plugin_dir()
        files = []

        for fname in os.listdir(PLUGIN_DIR):
            # 跳过元数据文件
            if fname.endswith('.meta.json'):
                continue

            desc = ''
            disp = fname

            # 查找对应的元数据文件
            meta_path = os.path.join(PLUGIN_DIR, fname + '.meta.json')
            if os.path.exists(meta_path):
                try:
                    import json as _json
                    with open(meta_path, 'r', encoding='utf-8') as mf:
                        meta = _json.load(mf)
                        desc = meta.get('description', '')
                        disp = meta.get('display_name', fname)
                except Exception as e:
                    print(f"读取元数据失败 {meta_path}: {e}")

            files.append({
                'name': fname,
                'url': settings.MEDIA_URL + 'plugins/' + escape_uri_path(fname),
                'description': desc,
                'display_name': disp
            })

        return APIResponse(code=0, msg='查询成功', data=files)

    except Exception as e:
        return APIResponse(code=1, msg=f'获取文件列表失败: {str(e)}')


@api_view(['GET'])
def download_exe(request):  # 注：现在支持所有文件类型，不仅限于exe
    filename = request.GET.get('name')
    if not filename:
        return JsonResponse({'error': '缺少文件名参数'}, status=400)

    # 安全检查
    if '..' in filename or '/' in filename or '\\' in filename:
        return JsonResponse({'error': '非法文件名'}, status=400)

    path = os.path.join(PLUGIN_DIR, filename)
    if not os.path.exists(path):
        return HttpResponseNotFound('文件不存在')

    try:
        response = FileResponse(
            open(path, 'rb'),
            as_attachment=True,  # 这个很重要，强制下载
            filename=filename
        )

        # 强制设置为下载模式
        response['Content-Type'] = 'application/octet-stream'  # 通用二进制类型
        response[
            'Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{escape_uri_path(filename)}'

        # 添加缓存控制
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response

    except Exception as e:
        return JsonResponse({'error': '文件下载失败'}, status=500)