#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件MD5备份脚本
扫描指定目录下所有文件，计算MD5值并保存到备份文件中
用于后续文件更新检测的基准数据

支持功能：
- 递归扫描指定目录下的所有文件
- 计算每个文件的MD5值和最后修改时间
- 将备份数据保存到文件中
- 将备份记录同步到数据库
- 支持大文件处理和进度报告
"""

import os
import sys
import time
import hashlib
import traceback
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
from script_base import ScriptBase, create_simple_script


# 延迟导入Django相关模块，避免循环导入问题
def get_django_models():
    """延迟导入Django模型，避免循环导入"""
    try:
        print("开始导入Django模块...")

        # 确保项目根目录在Python路径中
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)  # 上一级目录
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            print(f"已添加项目根目录到Python路径: {project_root}")

        # 设置Django环境
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

        import django
        from django.conf import settings

        # 检查Django是否已经初始化
        try:
            if not django.apps.apps.ready:
                print("正在初始化Django环境...")
                django.setup()
                print("Django环境初始化完成")
        except AttributeError:
            print("正在初始化Django环境（兼容模式）...")
            django.setup()
            print("Django环境初始化完成")
        except Exception as setup_error:
            print(f"Django初始化失败: {setup_error}")
            return None

        # 导入模型
        print("正在导入FileRecord模型...")
        from myapp.models import FileRecord
        print("FileRecord模型导入成功")

        # 测试数据库连接
        print("测试数据库连接...")
        from django.db import connection
        connection.ensure_connection()
        print("数据库连接正常")

        # 检查表是否存在
        table_name = FileRecord._meta.db_table
        with connection.cursor() as cursor:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"表 {table_name} 存在，当前记录数: {count}")
            except Exception as table_error:
                print(f"表 {table_name} 可能不存在或无法访问: {table_error}")
                return None

        return FileRecord

    except ImportError as e:
        print(f"导入模块失败: {e}")
        return None
    except Exception as e:
        print(f"Django模型导入失败: {e}")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"Python路径: {sys.path[:3]}...")  # 只显示前3个路径，避免过长
        print(f"错误详情: {str(e)}")
        return None


class BackupAssetsMD5Script:
    """文件MD5备份脚本类，支持多函数协作"""

    def __init__(self, script: ScriptBase):
        """初始化备份脚本"""
        self.script = script
        self.results = {}
        self.errors = []
        self.file_md5_data = []
        self.max_files_per_batch = 1000  # 限制批次大小，避免内存溢出

    def validate_parameters(self) -> bool:
        """验证输入参数"""
        try:
            # 获取参数（使用默认值）
            root_path = self.script.get_parameter('root_path', 'D:\\fishdev\\client\\MainProject\\Assets\\InBundle')

            # 验证路径是否存在
            if not os.path.exists(root_path):
                self.script.error(f"扫描目录不存在: {root_path}")
                return False

            if not os.path.isdir(root_path):
                self.script.error(f"扫描路径不是目录: {root_path}")
                return False

            self.script.info("参数验证通过")
            return True
        except Exception as e:
            self.script.error(f"参数验证时出错: {e}")
            return False

    def initialize_data(self) -> Dict[str, Any]:
        """初始化数据"""
        try:
            self.script.info("开始初始化数据")

            # 获取参数
            data = {
                'root_path': self.script.get_parameter('root_path',
                                                       'D:\\fishdev\\client\\MainProject\\Assets\\InBundle'),
                'backup_dir': self.script.get_parameter('backup_dir', '../upload/databackup'),
                'chunk_size': self.script.get_parameter('chunk_size', 8192),
                'timestamp': time.time()
            }

            self.script.debug(f"初始化数据完成")
            return data
        except Exception as e:
            self.script.error(f"初始化数据时出错: {e}")
            raise

    def find_all_files_in_path(self, root_path: str) -> List[str]:
        """
        递归扫描指定路径下的所有文件
        """
        try:
            all_files = []
            root_path_obj = Path(root_path)

            self.script.info(f"开始扫描目录: {root_path}")

            # 使用迭代器避免一次性加载所有文件到内存
            file_count = 0
            for file_path in root_path_obj.rglob('*'):
                if file_path.is_file():
                    all_files.append(str(file_path))
                    file_count += 1

                    # 每1000个文件报告一次进度，避免内存过度使用
                    if file_count % 1000 == 0:
                        self.script.info(f"已扫描 {file_count} 个文件...")
                        # 强制垃圾回收
                        gc.collect()

            self.script.info(f"扫描完成，找到 {len(all_files)} 个文件")
            return all_files

        except Exception as e:
            self.script.error(f"扫描文件时出错: {e}")
            raise

    def calculate_file_md5(self, file_path: str, chunk_size: int = 8192) -> Tuple[str, str, str]:
        """
        计算文件的MD5值
        """
        try:
            # 获取文件最后修改时间
            file_mtime = os.path.getmtime(file_path)
            file_last_update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_mtime))

            # 计算MD5值
            md5_hash = hashlib.md5()

            # 使用更安全的文件读取方式
            try:
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        md5_hash.update(chunk)
            except PermissionError:
                self.script.warning(f"权限不足，跳过文件: {file_path}")
                return file_path, file_last_update_time, "PERMISSION_DENIED"
            except Exception as read_error:
                self.script.warning(f"读取文件失败，跳过: {file_path} - {read_error}")
                return file_path, file_last_update_time, "READ_ERROR"

            md5_value = md5_hash.hexdigest()

            return file_path, file_last_update_time, md5_value

        except (IOError, OSError) as e:
            self.script.warning(f"文件访问失败 {file_path}: {e}")
            return file_path, "ERROR", "FILE_ACCESS_ERROR"
        except Exception as e:
            self.script.warning(f"计算MD5时出错 {file_path}: {e}")
            return file_path, "ERROR", "MD5_CALC_ERROR"

    def get_all_files_md5(self, file_paths: List[str], chunk_size: int = 8192) -> List[Tuple[str, str, str]]:
        """
        批量计算所有文件的MD5值
        """
        try:
            file_md5_data = []
            total_files = len(file_paths)

            self.script.info(f"开始计算 {total_files} 个文件的MD5值...")

            for i, file_path in enumerate(file_paths):
                try:
                    # 进度报告
                    if i % 50 == 0 or i == total_files - 1:  # 减少进度报告频率
                        progress = (i + 1) / total_files * 100
                        self.script.info(f"计算进度: {i + 1}/{total_files} ({progress:.1f}%)")

                    file_data = self.calculate_file_md5(file_path, chunk_size)
                    file_md5_data.append(file_data)

                    # 定期清理内存
                    if i % 100 == 0:
                        gc.collect()

                except Exception as e:
                    self.script.warning(f"跳过文件 {file_path}: {e}")
                    # 添加错误记录而不是跳过
                    file_md5_data.append((file_path, "ERROR", "PROCESSING_ERROR"))
                    continue

            self.script.info(f"MD5计算完成，处理了 {len(file_md5_data)} 个文件")
            return file_md5_data

        except Exception as e:
            self.script.error(f"批量计算MD5时出错: {e}")
            raise

    def save_backup_data(self, backup_data: List[Tuple[str, str, str]], backup_dir: str) -> str:
        """
        保存备份数据到文件
        """
        try:
            # 确保备份目录存在
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)

            # 生成备份文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            backup_filename = f"Assets_{timestamp}.txt"
            backup_file_path = backup_path / backup_filename

            # 保存数据 - 使用更安全的方式
            self.script.info(f"开始保存 {len(backup_data)} 条记录到文件...")

            with open(backup_file_path, 'w', encoding='utf-8') as f:
                # 分批写入，避免内存问题
                for i, data_item in enumerate(backup_data):
                    f.write(str(data_item) + '\n')
                    if i % 1000 == 0:
                        f.flush()  # 定期刷新缓冲区

            self.script.info(f"备份数据已保存到: {backup_file_path}")
            return str(backup_file_path)

        except Exception as e:
            self.script.error(f"保存备份数据时出错: {e}")
            raise

    def save_backup_record_to_db(self, backup_file_path: str, root_path: str) -> bool:
        """
        将备份文件记录保存到autotest数据库的c_file_records表中
        """
        try:
            # 解析备份文件路径
            backup_path_obj = Path(backup_file_path)
            backup_file_name = backup_path_obj.name

            # 获取当前时间
            backup_time = datetime.now()

            self.script.info(f"开始保存备份文件记录到数据库...")
            self.script.info(f"备份文件名: {backup_file_name}")
            self.script.info(f"扫描路径: {root_path}")

            # 延迟导入Django模型
            self.script.info("正在导入Django模型...")
            FileRecord = get_django_models()
            if FileRecord is None:
                self.script.error("无法导入Django模型，跳过数据库保存")
                return False

            self.script.info("Django模型导入成功，开始保存数据...")

            # 使用事务确保数据保存
            from django.db import transaction, connection

            try:
                # 检查数据库连接状态
                connection.ensure_connection()
                self.script.info("数据库连接确认正常")

                # 准备保存的数据
                save_data = {
                    'backup_time': backup_time,
                    'backup_file_name': backup_file_name,
                    'backup_path': root_path
                }

                self.script.info(f"准备保存的数据: {save_data}")

                # 使用事务保存数据
                with transaction.atomic():
                    file_record = FileRecord.objects.create(**save_data)
                    self.script.info(f"数据库记录创建成功，ID: {file_record.id}")

                # 验证保存结果
                saved_record = FileRecord.objects.filter(id=file_record.id).first()
                if saved_record:
                    self.script.info(f"✓ 数据库保存验证成功，记录ID: {saved_record.id}")
                    return True
                else:
                    self.script.error("✗ 数据库保存验证失败")
                    return False

            except Exception as db_error:
                self.script.error(f"数据库操作失败: {db_error}")
                return False

        except Exception as e:
            self.script.error(f"保存备份记录到数据库时出错: {e}")
            return False

    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据"""
        try:
            self.script.info("开始处理数据")

            # 1. 扫描所有文件
            all_files = self.find_all_files_in_path(data['root_path'])
            if not all_files:
                raise ValueError("未找到任何文件")

            # 2. 计算所有文件的MD5值
            file_md5_data = self.get_all_files_md5(all_files, data['chunk_size'])
            if not file_md5_data:
                raise ValueError("未成功计算任何文件的MD5值")

            # 3. 保存备份数据
            backup_file_path = self.save_backup_data(file_md5_data, data['backup_dir'])

            # 4. 保存备份记录到数据库
            db_save_success = self.save_backup_record_to_db(backup_file_path, data['root_path'])

            # 5. 计算统计信息
            total_files = len(file_md5_data)
            backup_size = os.path.getsize(backup_file_path)
            backup_size_mb = backup_size / (1024 * 1024)

            processed_data = {
                'total_files': total_files,
                'backup_file': backup_file_path,
                'backup_size': backup_size,
                'backup_size_mb': round(backup_size_mb, 2),
                'scan_directory': data['root_path'],
                'backup_timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                'database_record_saved': db_save_success,
                'success_count': len(
                    [x for x in file_md5_data if x[2] not in ['ERROR', 'PERMISSION_DENIED', 'READ_ERROR']]),
                'error_count': len([x for x in file_md5_data if x[2] in ['ERROR', 'PERMISSION_DENIED', 'READ_ERROR']])
            }

            self.script.info(
                f"数据处理完成: 成功 {processed_data['success_count']}, 错误 {processed_data['error_count']}")
            return processed_data

        except Exception as e:
            self.script.error(f"数据处理失败: {e}")
            raise

    def validate_results(self, data: Dict[str, Any]) -> bool:
        """验证处理结果"""
        try:
            self.script.info("开始验证结果")

            # 验证基本结果
            if not data.get('total_files', 0) > 0:
                self.script.error("处理结果验证失败: 没有处理任何文件")
                return False

            if not data.get('backup_file'):
                self.script.error("处理结果验证失败: 备份文件路径为空")
                return False

            if not os.path.exists(data['backup_file']):
                self.script.error("处理结果验证失败: 备份文件不存在")
                return False

            if data.get('backup_size', 0) <= 0:
                self.script.warning("备份文件大小异常")

            self.script.info("结果验证通过")
            return True
        except Exception as e:
            self.script.error(f"结果验证时出错: {e}")
            return False

    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告"""
        try:
            self.script.info("开始生成报告")

            # 生成结果消息
            message = f"文件MD5备份完成\n"
            message += f"扫描目录: {data['scan_directory']}\n"
            message += f"备份文件: {os.path.basename(data['backup_file'])}\n"
            message += f"文件数量: {data['total_files']}\n"
            message += f"成功处理: {data.get('success_count', 0)}\n"
            message += f"处理失败: {data.get('error_count', 0)}\n"
            message += f"备份大小: {data['backup_size_mb']:.2f} MB\n"
            message += f"数据库记录: {'已保存' if data['database_record_saved'] else '保存失败'}"

            # 生成详细报告
            report = {
                'summary': {
                    'total_files': data['total_files'],
                    'success_count': data.get('success_count', 0),
                    'error_count': data.get('error_count', 0),
                    'backup_size_mb': data['backup_size_mb'],
                    'database_saved': data['database_record_saved'],
                    'status': 'completed'
                },
                'backup_info': {
                    'backup_file': data['backup_file'],
                    'scan_directory': data['scan_directory'],
                    'backup_timestamp': data['backup_timestamp']
                },
                'metadata': {
                    'script_name': 'backupAssetsMD5',
                    'execution_time': time.time(),
                    'version': '1.0.1'
                }
            }

            self.script.info("报告生成完成")
            return report
        except Exception as e:
            self.script.error(f"生成报告时出错: {e}")
            raise

    def cleanup(self):
        """清理资源"""
        try:
            self.script.info("开始清理资源")

            # 清理临时数据
            self.file_md5_data = []
            self.results = {}
            self.errors = []

            # 强制垃圾回收
            gc.collect()

            self.script.info("资源清理完成")
        except Exception as e:
            self.script.warning(f"资源清理时出错: {e}")

    def run(self) -> Dict[str, Any]:
        """执行完整的脚本流程"""
        try:
            self.script.info("开始执行文件MD5备份脚本")

            # 1. 参数验证
            if not self.validate_parameters():
                return self.script.error_result("参数验证失败", "ValidationError")

            # 2. 初始化数据
            data = self.initialize_data()

            # 3. 处理数据
            processed_data = self.process_data(data)

            # 4. 验证结果
            if not self.validate_results(processed_data):
                return self.script.error_result("结果验证失败", "ValidationError")

            # 5. 生成报告
            report = self.generate_report(processed_data)

            # 6. 清理资源
            self.cleanup()

            # 7. 返回成功结果
            success_message = f"备份完成: {processed_data['total_files']} 个文件, {processed_data['backup_size_mb']:.2f} MB"
            return self.script.success_result(
                message=success_message,
                data=report
            )

        except Exception as e:
            self.script.error(f"脚本执行失败: {e}")
            self.script.error(f"错误详情: {traceback.format_exc()}")

            # 确保清理资源
            try:
                self.cleanup()
            except:
                pass

            return self.script.error_result(f"执行失败: {str(e)}", "ExecutionError")


def main_logic(script: ScriptBase) -> Dict[str, Any]:
    """主入口函数 - 使用高级脚本类"""
    # 创建备份脚本实例
    backup_script = BackupAssetsMD5Script(script)

    # 执行脚本
    return backup_script.run()


if __name__ == '__main__':
    try:
        print("启动文件MD5备份脚本...")

        # 创建脚本实例
        create_simple_script('backupAssetsMD5', main_logic)

        print("脚本执行完成")

    except Exception as e:
        print(f"脚本启动失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        sys.exit(1)