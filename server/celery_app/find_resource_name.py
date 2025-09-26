#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件内容搜索脚本 - 在指定文件中搜索目标字符串
支持在文件内容中搜索指定字符串，支持多种匹配规则
"""

import os
import chardet
from typing import List, Tuple, Dict, Any
from script_base import ScriptBase, create_simple_script


class FileContentSearcher:
    """文件内容搜索器"""
    
    def __init__(self, script: ScriptBase):
        """初始化查找器"""
        self.script = script
        self.results = []
        
    def validate_parameters(self) -> bool:
        """验证输入参数"""
        required_params = ['search_string', 'target_files', 'file_formats', 'match_rules']
        
        for param in required_params:
            if not self.script.get_parameter(param):
                self.script.error(f"缺少必需参数: {param}")
                return False
                
        self.script.info("参数验证通过")
        return True
    
    def get_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            with open(file_path, 'rb') as f:
                result = chardet.detect(f.read())
                return result['encoding'] or 'utf-8'
        except Exception as e:
            self.script.warning(f"无法检测文件编码 {file_path}: {e}")
            return 'utf-8'
    
    def read_file_with_chardet(self, file_path: str) -> str:
        """读取文件内容，自动检测编码"""
        try:
            encoding = self.get_encoding(file_path)
            with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                return file.read()
        except Exception as e:
            self.script.error(f"读取文件失败 {file_path}: {e}")
            return None
    
    def find_files(self, directory: str, file_formats: List[str], recursive: bool = True) -> List[str]:
        """查找指定格式的文件"""
        files = []
        try:
            if recursive:
                # 递归搜索所有子目录
                for root, dirs, filenames in os.walk(directory):
                    for filename in filenames:
                        # 检查文件是否匹配指定的格式
                        if any(filename.endswith(fmt) for fmt in file_formats):
                            file_path = os.path.join(root, filename)
                            files.append(file_path)
            else:
                # 只搜索指定目录的直接文件
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        # 检查文件是否匹配指定的格式
                        if any(filename.endswith(fmt) for fmt in file_formats):
                            files.append(file_path)
        except Exception as e:
            self.script.error(f"遍历目录失败 {directory}: {e}")
        
        return files
    
    def search_in_file_content(self, content: str, search_string: str, match_rules: List[str]) -> List[str]:
        """在文件内容中搜索字符串"""
        results = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # 根据匹配规则进行搜索
            if self.match_string(line, search_string, match_rules):
                results.append(f"第{line_num}行: {line.strip()}")
        
        return results
    
    def match_string(self, text: str, search_string: str, match_rules: List[str]) -> bool:
        """根据匹配规则检查字符串是否匹配"""
        if not match_rules:
            return search_string in text
        
        for rule in match_rules:
            if rule == "全匹配" or rule == "exact_match":
                # 全匹配：字符串必须完全相等
                if text == search_string:
                    return True
            elif rule == "前缀匹配" or rule == "prefix_match":
                # 前缀匹配：字符串以搜索词开头
                if text.startswith(search_string):
                    return True
            elif rule == "后缀匹配" or rule == "suffix_match":
                # 后缀匹配：字符串以搜索词结尾
                if text.endswith(search_string):
                    return True
            elif rule == "包含匹配" or rule == "contains_match":
                # 包含匹配：字符串包含搜索词
                if search_string in text:
                    return True
        
        return False
    
    def search_in_directory(self, directory: str, search_string: str, file_formats: List[str], match_rules: List[str], recursive: bool = True) -> List[Dict[str, Any]]:
        """在目录中的文件中搜索字符串"""
        self.script.info(f"开始在目录中搜索: {directory}")
        
        files = self.find_files(directory, file_formats, recursive)
        results = []
        
        for file_path in files:
            try:
                content = self.read_file_with_chardet(file_path)
                if content:
                    matches = self.search_in_file_content(content, search_string, match_rules)
                    
                    if matches:
                        file_ext = os.path.splitext(file_path)[1]
                        file_type = 'script' if file_ext in ['.cs', '.py', '.js', '.ts'] else 'config'
                        
                        results.append({
                            'type': file_type,
                            'filename': os.path.basename(file_path),
                            'filepath': file_path,
                            'matches': matches
                        })
            except Exception as e:
                self.script.warning(f"搜索文件失败 {file_path}: {e}")
        
        return results
    
    
    def get_project_paths(self) -> Dict[str, str]:
        """获取项目路径配置"""
        # 从参数中获取目标搜索文件路径
        target_files = self.script.get_parameter('target_files', [])
        
        # 处理参数类型问题：如果是字符串，转换为列表
        if isinstance(target_files, str):
            target_files = [target_files]
        
        if not target_files:
            self.script.error("必须指定目标搜索文件或目录")
            return {}
        
        # 使用指定的目标文件路径
        return {
            'target_paths': target_files
        }
    
    def run_search(self) -> Dict[str, Any]:
        """执行搜索"""
        search_string = self.script.get_parameter('search_string')
        target_files = self.script.get_parameter('target_files', [])
        file_formats = self.script.get_parameter('file_formats', ['.txt', '.cs'])
        match_rules = self.script.get_parameter('match_rules', ['包含匹配'])
        
        # 添加调试信息
        self.script.info(f"搜索参数 - 搜索字符串: {search_string}")
        self.script.info(f"搜索参数 - 目标文件: {target_files}")
        self.script.info(f"搜索参数 - 文件格式: {file_formats}")
        self.script.info(f"搜索参数 - 匹配规则: {match_rules}")
        
        paths = self.get_project_paths()
        if not paths:
            return {
                'search_string': search_string,
                'target_files': target_files,
                'file_formats': file_formats,
                'match_rules': match_rules,
                'config_results': [],
                'script_results': [],
                'total_matches': 0
            }
        
        results = {
            'search_string': search_string,
            'target_files': target_files,
            'file_formats': file_formats,
            'match_rules': match_rules,
            'config_results': [],
            'script_results': [],
            'total_matches': 0
        }
        
        # 在指定的目标文件路径中搜索
        self.script.info(f"目标路径列表: {paths['target_paths']}")
        for i, target_path in enumerate(paths['target_paths']):
            self.script.info(f"正在搜索路径 {i+1}/{len(paths['target_paths'])}: {target_path}")
            self.script.info(f"路径类型检查: 存在={os.path.exists(target_path)}, 是文件={os.path.isfile(target_path) if os.path.exists(target_path) else 'N/A'}, 是目录={os.path.isdir(target_path) if os.path.exists(target_path) else 'N/A'}")
            if os.path.exists(target_path):
                if os.path.isfile(target_path):
                    self.script.info(f"搜索单个文件: {target_path}")
                    # 单个文件搜索
                    content = self.read_file_with_chardet(target_path)
                    if content:
                        lines = content.splitlines()
                        matches = []
                        for line_num, line in enumerate(lines, 1):
                            if self.match_string(line, search_string, match_rules):
                                matches.append(f"第{line_num}行: {line.strip()}")
                        
                        if matches:
                            file_ext = os.path.splitext(target_path)[1]
                            if file_ext in ['.cs', '.py', '.js', '.ts']:
                                results['script_results'].append({
                                    'type': 'script',
                                    'filename': os.path.basename(target_path),
                                    'filepath': target_path,
                                    'matches': matches
                                })
                            else:
                                results['config_results'].append({
                                    'type': 'config',
                                    'filename': os.path.basename(target_path),
                                    'filepath': target_path,
                                    'matches': matches
                                })
                elif os.path.isdir(target_path):
                    self.script.info(f"搜索目录: {target_path}")
                    # 目录搜索
                    directory_results = self.search_in_directory(target_path, search_string, file_formats, match_rules)
                    self.script.info(f"目录搜索结果数量: {len(directory_results)}")
                    results['config_results'].extend([r for r in directory_results if r['type'] == 'config'])
                    results['script_results'].extend([r for r in directory_results if r['type'] == 'script'])
            else:
                self.script.warning(f"目标路径不存在: {target_path}")
        
        results['total_matches'] = len(results['config_results']) + len(results['script_results'])
        return results
    
    def generate_report(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成搜索报告"""
        self.script.info("生成搜索报告")
        
        # 构建详细的搜索结果消息
        message_parts = []
        
        # 添加搜索摘要
        message_parts.append(f"搜索字符串: {search_results['search_string']}")
        message_parts.append(f"匹配规则: {', '.join(search_results['match_rules'])}")
        message_parts.append(f"文件格式: {', '.join(search_results['file_formats'])}")
        message_parts.append(f"总匹配数: {search_results['total_matches']}")
        message_parts.append("")
        
        # 添加配置文件结果
        if search_results['config_results']:
            message_parts.append("=== 配置文件搜索结果 ===")
            for result in search_results['config_results']:
                message_parts.append(f"文件: {result['filename']}")
                message_parts.append(f"路径: {result['filepath']}")
                message_parts.append("匹配内容:")
                for match in result['matches']:
                    message_parts.append(f"  {match}")
                message_parts.append("")
        
        # 添加脚本文件结果
        if search_results['script_results']:
            message_parts.append("=== 脚本文件搜索结果 ===")
            for result in search_results['script_results']:
                message_parts.append(f"文件: {result['filename']}")
                message_parts.append(f"路径: {result['filepath']}")
                message_parts.append("匹配内容:")
                for match in result['matches']:
                    message_parts.append(f"  {match}")
                message_parts.append("")
        
        # 如果没有找到匹配
        if search_results['total_matches'] == 0:
            message_parts.append("未找到匹配的内容")
        
        # 合并所有消息
        detailed_message = "\n".join(message_parts)
        
        report = {
            'summary': {
                'search_string': search_results['search_string'],
                'target_files': search_results['target_files'],
                'file_formats': search_results['file_formats'],
                'match_rules': search_results['match_rules'],
                'total_matches': search_results['total_matches'],
                'config_files_found': len(search_results['config_results']),
                'script_files_found': len(search_results['script_results'])
            },
            'config_results': search_results['config_results'],
            'script_results': search_results['script_results'],
            'detailed_message': detailed_message,
            'metadata': {
                'script_name': self.script.script_name,
                'execution_context': self.script.page_context
            }
        }
        
        return report
    
    def run(self) -> Dict[str, Any]:
        """执行完整的搜索流程"""
        try:
            # 1. 参数验证
            if not self.validate_parameters():
                return self.script.error_result("参数验证失败", "ValidationError")
            
            # 2. 执行搜索
            search_results = self.run_search()
            
            # 3. 生成报告
            report = self.generate_report(search_results)
            
            # 4. 返回结果
            if search_results['total_matches'] > 0:
                return self.script.success_result(
                    message=report['detailed_message'],
                    data=report
                )
            else:
                return self.script.success_result(
                    message=report['detailed_message'],
                    data=report
                )
            
        except Exception as e:
            self.script.error(f"搜索执行失败: {e}")
            raise


def main_logic(script: ScriptBase) -> Dict[str, Any]:
    """主入口函数"""
    # 创建文件内容搜索器实例
    searcher = FileContentSearcher(script)
    
    # 执行搜索
    return searcher.run()


if __name__ == '__main__':
    # 使用模板创建脚本
    create_simple_script('find_resource_name', main_logic)