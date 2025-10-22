#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件更新对比脚本
对比当前目录文件与历史备份文件，检测文件的更新、删除、新增情况
按照advanced_script_template.py模板重构
"""

import os
import sys
import time
import hashlib
import ast
import traceback
from pathlib import Path
from typing import Dict, Any
import os
import sys

# 添加当前目录到Python路径，确保可以导入script_base
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

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


class CompareAssetsUpdateScript:
    """文件更新对比脚本类，支持多函数协作"""

    def __init__(self, script: ScriptBase):
        """初始化文件对比脚本"""
        self.script = script
        self.results = {}
        self.errors = []

    def validate_parameters(self) -> bool:
        """验证输入参数"""
        self.script.info("开始验证参数...")

        # 获取参数（包括默认值）
        root_path = self.script.get_parameter('root_path', 'D:\\fishdev\\client\\MainProject\\Assets\\InBundle')
        backup_dir = self.script.get_parameter('backup_dir', '../upload/databackup')
        output_dir = self.script.get_parameter('output_dir', './result/domesticLogs/checkAssetsUpdateLogs')
        chunk_size = self.script.get_parameter('chunk_size', 8192)

        # 验证关键路径
        if not root_path or not isinstance(root_path, str):
            self.script.error("root_path 参数无效")
            return False

        if not os.path.exists(root_path):
            self.script.error(f"扫描目录不存在: {root_path}")
            return False

        if not os.path.isdir(root_path):
            self.script.error(f"扫描路径不是目录: {root_path}")
            return False

        self.script.info(f"参数验证通过")
        self.script.info(f"扫描目录: {root_path}")
        self.script.info(f"备份目录: {backup_dir}")
        self.script.info(f"输出目录: {output_dir}")
        self.script.info(f"块大小: {chunk_size}")

        return True

    def initialize_data(self) -> Dict[str, Any]:
        """初始化数据"""
        self.script.info("开始初始化数据")

        # 获取参数
        data = {
            'root_path': self.script.get_parameter('root_path', 'D:\\fishdev\\client\\MainProject\\Assets\\InBundle'),
            'backup_dir': self.script.get_parameter('backup_dir', '../upload/databackup'),
            'output_dir': self.script.get_parameter('output_dir', './result/domesticLogs/checkAssetsUpdateLogs'),
            'chunk_size': self.script.get_parameter('chunk_size', 8192),
            'timestamp': time.time()
        }

        self.script.debug(f"初始化数据: {data}")
        return data

    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据 - 核心文件对比逻辑"""
        self.script.info("开始处理数据")

        try:
            # 1. 从数据库获取最近备份文件
            backup_file = self.get_latest_backup_file(data['backup_dir'])
            data['backup_file'] = backup_file

            # 2. 加载历史备份数据
            backup_data = self.load_backup_data(backup_file)
            data['backup_data'] = backup_data

            # 3. 扫描当前目录文件
            current_files = self.find_all_files_in_path(data['root_path'])
            data['current_files'] = current_files

            # 4. 对比文件变化
            comparison_result = self.compare_files(current_files, backup_data, data['chunk_size'])
            data['comparison_result'] = comparison_result

            # 5. 生成对比结果摘要（不保存文件）
            comparison_summary = self.generate_comparison_summary(comparison_result)
            data['comparison_summary'] = comparison_summary

            self.script.debug(f"数据处理完成")
            return data

        except Exception as e:
            self.script.error(f"数据处理失败: {e}")
            raise

    def validate_results(self, data: Dict[str, Any]) -> bool:
        """验证处理结果"""
        self.script.info("开始验证结果")

        # 验证关键结果
        if not data.get('comparison_result'):
            self.script.error("处理结果验证失败: 对比结果为空")
            return False

        if not data.get('backup_file'):
            self.script.error("处理结果验证失败: 备份文件路径为空")
            return False

        if not data.get('comparison_summary'):
            self.script.warning("对比结果摘要为空")

        self.script.info("结果验证通过")
        return True

    def generate_comparison_summary(self, comparison_result: dict) -> str:
        """生成对比结果摘要"""
        total_updated = len(comparison_result['updated_files'])
        total_deleted = len(comparison_result['deleted_files'])
        total_added = len(comparison_result['added_files'])
        total_unchanged = len(comparison_result['unchanged_files'])
        total_changes = total_updated + total_deleted + total_added

        summary_lines = []
        summary_lines.append("=" * 60)
        summary_lines.append("文件更新检测结果")
        summary_lines.append("=" * 60)
        summary_lines.append(f"检测时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
        summary_lines.append("")

        # 统计信息
        summary_lines.append("=== 变化统计 ===")
        summary_lines.append(f"更新文件: {total_updated} 个")
        summary_lines.append(f"删除文件: {total_deleted} 个")
        summary_lines.append(f"新增文件: {total_added} 个")
        summary_lines.append(f"未变化文件: {total_unchanged} 个")
        summary_lines.append(f"总变化数: {total_changes} 个")
        summary_lines.append("")

        # 更新文件详情
        if comparison_result['updated_files']:
            summary_lines.append("=== 更新文件列表 ===")
            for i, file_info in enumerate(comparison_result['updated_files'], 1):
                summary_lines.append(f"{i}. {file_info['file_path']}")
                summary_lines.append(f"   旧MD5: {file_info['old_md5']}")
                summary_lines.append(f"   新MD5: {file_info['new_md5']}")
                summary_lines.append(f"   更新时间: {file_info['new_update_time']}")
                summary_lines.append("")

        # 新增文件详情
        if comparison_result['added_files']:
            summary_lines.append("=== 新增文件列表 ===")
            for i, file_info in enumerate(comparison_result['added_files'], 1):
                summary_lines.append(f"{i}. {file_info['file_path']}")
                summary_lines.append(f"   MD5: {file_info['md5_value']}")
                summary_lines.append(f"   创建时间: {file_info['update_time']}")
                summary_lines.append("")

        # 删除文件详情
        if comparison_result['deleted_files']:
            summary_lines.append("=== 删除文件列表 ===")
            for i, file_info in enumerate(comparison_result['deleted_files'], 1):
                summary_lines.append(f"{i}. {file_info['file_path']}")
                summary_lines.append(f"   最后更新: {file_info['last_update_time']}")
                summary_lines.append(f"   最后MD5: {file_info['last_md5']}")
                summary_lines.append("")

        return '\n'.join(summary_lines)

    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告"""
        self.script.info("开始生成报告")

        comparison_result = data['comparison_result']
        total_updated = len(comparison_result['updated_files'])
        total_deleted = len(comparison_result['deleted_files'])
        total_added = len(comparison_result['added_files'])
        total_unchanged = len(comparison_result['unchanged_files'])
        total_changes = total_updated + total_deleted + total_added

        # 生成消息
        if total_changes == 0:
            message = f"文件更新对比完成 - 没有发现任何变化\n"
            message += f"扫描目录: {data['root_path']}\n"
            message += f"备份文件: {os.path.basename(data['backup_file'])}\n"
            message += f"未变化文件: {total_unchanged} 个\n"
            message += f"所有文件与备份文件完全一致"
        else:
            message = f"文件更新对比完成 - 发现 {total_changes} 个变化\n"
            message += f"扫描目录: {data['root_path']}\n"
            message += f"备份文件: {os.path.basename(data['backup_file'])}\n"
            message += f"更新文件: {total_updated} 个\n"
            message += f"删除文件: {total_deleted} 个\n"
            message += f"新增文件: {total_added} 个\n"
            message += f"未变化文件: {total_unchanged} 个\n"
            message += f"总变化数: {total_changes} 个"

        # 生成报告数据
        report = {
            'summary': {
                'scan_directory': data['root_path'],
                'backup_file': data['backup_file'],
                'total_files': len(data['current_files']),
                'updated_files': total_updated,
                'deleted_files': total_deleted,
                'added_files': total_added,
                'unchanged_files': total_unchanged,
                'total_changes': total_changes,
                'comparison_timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            },
            'details': comparison_result,
            'comparison_summary': data.get('comparison_summary', ''),
            'metadata': {
                'script_name': self.script.script_name,
                'execution_time': time.time(),
                'version': '1.0.0'
            },
            'message': message
        }

        self.script.debug(f"报告生成完成")
        return report

    def cleanup(self):
        """清理资源"""
        self.script.info("开始清理资源")
        # 文件对比脚本通常不需要特殊清理
        self.script.info("资源清理完成")

    def run(self) -> Dict[str, Any]:
        """执行完整的脚本流程"""
        try:
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

            # 7. 输出对比结果摘要
            if report.get('comparison_summary'):
                self.script.info("对比结果摘要:")
                print("\n" + report['comparison_summary'] + "\n")

            # 8. 返回成功结果
            return self.script.success_result(
                message=report['message'],
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
            return self.script.error_result(f"对比失败: {e}", "ScriptError")

    # 以下是原有的辅助方法，现在作为类方法
    def get_latest_backup_file(self, backup_dir: str) -> str:
        """从数据库获取最近一次备份的文件名，并在指定目录中查找该文件"""
        try:
            self.script.info("开始从数据库获取最近备份文件...")

            # 导入Django模型
            FileRecord = get_django_models()
            if FileRecord is None:
                raise Exception("无法导入Django模型")

            # 查询最近一次备份记录
            latest_record = FileRecord.objects.order_by('-backup_time').first()

            if not latest_record:
                raise Exception("数据库中没有找到任何备份记录")

            self.script.info(f"找到最近备份记录: {latest_record.backup_file_name}")
            self.script.info(f"备份时间: {latest_record.backup_time}")
            self.script.info(f"备份路径: {latest_record.backup_path}")

            # 构建备份文件完整路径
            backup_file_path = os.path.join(backup_dir, latest_record.backup_file_name)

            if not os.path.exists(backup_file_path):
                raise FileNotFoundError(f"备份文件不存在: {backup_file_path}")

            self.script.info(f"找到备份文件: {backup_file_path}")
            return backup_file_path

        except Exception as e:
            self.script.error(f"获取最近备份文件失败: {e}")
            raise

    def load_backup_data(self, backup_file_path: str) -> list:
        """加载历史备份数据"""
        try:
            if not os.path.exists(backup_file_path):
                raise FileNotFoundError(f"备份文件不存在: {backup_file_path}")

            self.script.info(f"加载历史备份数据: {backup_file_path}")

            backup_data = []
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:  # 跳过空行
                        continue

                    try:
                        # 解析每一行的元组数据
                        item = ast.literal_eval(line)
                        backup_data.append(item)
                    except (ValueError, SyntaxError) as e:
                        self.script.warning(f"跳过第 {line_num} 行无效数据: {line[:50]}... (错误: {e})")
                        continue

            if not backup_data:
                raise ValueError("备份文件中没有有效数据")

            self.script.info(f"成功加载 {len(backup_data)} 条历史记录")
            return backup_data

        except Exception as e:
            self.script.error(f"加载备份数据失败: {e}")
            raise

    def find_all_files_in_path(self, root_path: str) -> list:
        """递归扫描指定路径下的所有文件"""
        try:
            all_files = []
            root_path_obj = Path(root_path)

            if not root_path_obj.exists():
                raise FileNotFoundError(f"目录不存在: {root_path}")

            if not root_path_obj.is_dir():
                raise ValueError(f"路径不是目录: {root_path}")

            self.script.info(f"开始扫描当前目录: {root_path}")

            for file_path in root_path_obj.rglob('*'):
                if file_path.is_file():
                    all_files.append(str(file_path))

            self.script.info(f"扫描完成，找到 {len(all_files)} 个文件")
            return all_files

        except Exception as e:
            self.script.error(f"扫描文件时出错: {e}")
            raise

    def calculate_file_md5(self, file_path: str, chunk_size: int = 8192) -> str:
        """计算文件的MD5值"""
        try:
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    md5_hash.update(chunk)

            return md5_hash.hexdigest()

        except (IOError, OSError) as e:
            self.script.error(f"读取文件失败 {file_path}: {e}")
            raise
        except Exception as e:
            self.script.error(f"计算MD5时出错 {file_path}: {e}")
            raise

    def compare_files(self, current_files: list, backup_data: list, chunk_size: int = 8192) -> dict:
        """对比当前文件与历史备份数据"""
        try:
            self.script.info("开始对比文件变化...")

            # 创建历史文件路径集合，便于快速查找
            history_files = set()
            history_data_map = {}

            for item in backup_data:
                if len(item) >= 3:
                    file_path, update_time, md5_value = item[0], item[1], item[2]
                    history_files.add(file_path)
                    history_data_map[file_path] = {
                        'update_time': update_time,
                        'md5_value': md5_value
                    }

            # 创建当前文件路径集合
            current_files_set = set(current_files)

            # 初始化结果
            result = {
                'updated_files': [],
                'deleted_files': [],
                'added_files': [],
                'unchanged_files': []
            }

            # 检查历史文件的变化情况
            for file_path in history_files:
                try:
                    if file_path in current_files_set:
                        # 文件仍然存在，检查是否更新
                        current_md5 = self.calculate_file_md5(file_path, chunk_size)
                        history_md5 = history_data_map[file_path]['md5_value']

                        if current_md5 != history_md5:
                            # 文件已更新
                            current_mtime = os.path.getmtime(file_path)
                            current_update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_mtime))

                            result['updated_files'].append({
                                'file_path': file_path,
                                'old_md5': history_md5,
                                'new_md5': current_md5,
                                'old_update_time': history_data_map[file_path]['update_time'],
                                'new_update_time': current_update_time
                            })

                            self.script.debug(f"文件已更新: {os.path.basename(file_path)}")
                        else:
                            # 文件未变化
                            result['unchanged_files'].append({
                                'file_path': file_path,
                                'md5_value': current_md5,
                                'update_time': history_data_map[file_path]['update_time']
                            })

                        # 从当前文件集合中移除，剩余的就是新增文件
                        current_files_set.remove(file_path)
                    else:
                        # 文件被删除
                        result['deleted_files'].append({
                            'file_path': file_path,
                            'last_update_time': history_data_map[file_path]['update_time'],
                            'last_md5': history_data_map[file_path]['md5_value']
                        })

                        self.script.debug(f"文件已删除: {os.path.basename(file_path)}")

                except Exception as e:
                    self.script.warning(f"检查文件时出错 {file_path}: {e}")
                    continue

            # 剩余的文件都是新增的
            for file_path in current_files_set:
                try:
                    current_md5 = self.calculate_file_md5(file_path, chunk_size)
                    current_mtime = os.path.getmtime(file_path)
                    current_update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_mtime))

                    result['added_files'].append({
                        'file_path': file_path,
                        'md5_value': current_md5,
                        'update_time': current_update_time
                    })

                    self.script.debug(f"新增文件: {os.path.basename(file_path)}")

                except Exception as e:
                    self.script.warning(f"处理新增文件时出错 {file_path}: {e}")
                    continue

            self.script.info("文件对比完成")
            return result

        except Exception as e:
            self.script.error(f"对比文件时出错: {e}")
            raise

    def save_comparison_result(self, comparison_result: dict, output_dir: str) -> str:
        """保存对比结果到文件"""
        try:
            # 确保输出目录存在
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 生成输出文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            output_filename = f"checkAssetsUpdateLog_{timestamp}.txt"
            output_file_path = output_path / output_filename

            # 生成报告内容
            report_lines = []
            report_lines.append("=" * 80)
            report_lines.append("文件更新检测报告")
            report_lines.append("=" * 80)
            report_lines.append(f"检测时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
            report_lines.append("")

            # 统计信息
            total_updated = len(comparison_result['updated_files'])
            total_deleted = len(comparison_result['deleted_files'])
            total_added = len(comparison_result['added_files'])
            total_unchanged = len(comparison_result['unchanged_files'])
            total_changes = total_updated + total_deleted + total_added

            report_lines.append("=== 变化统计 ===")
            report_lines.append(f"更新文件: {total_updated} 个")
            report_lines.append(f"删除文件: {total_deleted} 个")
            report_lines.append(f"新增文件: {total_added} 个")
            report_lines.append(f"未变化文件: {total_unchanged} 个")
            report_lines.append(f"总变化数: {total_changes} 个")
            report_lines.append("")

            # 更新文件详情
            if comparison_result['updated_files']:
                report_lines.append("=== 更新文件列表 ===")
                for i, file_info in enumerate(comparison_result['updated_files'], 1):
                    report_lines.append(f"{i}. {file_info['file_path']}")
                    report_lines.append(f"   旧MD5: {file_info['old_md5']}")
                    report_lines.append(f"   新MD5: {file_info['new_md5']}")
                    report_lines.append(f"   更新时间: {file_info['new_update_time']}")
                    report_lines.append("")

            # 新增文件详情
            if comparison_result['added_files']:
                report_lines.append("=== 新增文件列表 ===")
                for i, file_info in enumerate(comparison_result['added_files'], 1):
                    report_lines.append(f"{i}. {file_info['file_path']}")
                    report_lines.append(f"   MD5: {file_info['md5_value']}")
                    report_lines.append(f"   创建时间: {file_info['update_time']}")
                    report_lines.append("")

            # 删除文件详情
            if comparison_result['deleted_files']:
                report_lines.append("=== 删除文件列表 ===")
                for i, file_info in enumerate(comparison_result['deleted_files'], 1):
                    report_lines.append(f"{i}. {file_info['file_path']}")
                    report_lines.append(f"   最后更新: {file_info['last_update_time']}")
                    report_lines.append(f"   最后MD5: {file_info['last_md5']}")
                    report_lines.append("")

            # 保存报告
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))

            self.script.info(f"对比结果已保存到: {output_file_path}")
            return str(output_file_path)

        except Exception as e:
            self.script.error(f"保存对比结果时出错: {e}")
            raise


def main_logic(script: ScriptBase) -> Dict[str, Any]:
    """主入口函数 - 使用高级脚本类"""
    # 创建文件对比脚本实例
    compare_script = CompareAssetsUpdateScript(script)

    # 执行脚本
    return compare_script.run()


if __name__ == '__main__':
    create_simple_script('compareAssetsUpdate', main_logic)