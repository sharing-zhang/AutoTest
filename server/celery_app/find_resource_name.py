#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源名称查找脚本 - 在项目中查找资源名称
支持在配置文件和脚本文件中搜索指定字符串
"""

import os
import chardet
from typing import List, Tuple, Dict, Any
from script_base import ScriptBase, create_simple_script


class ResourceNameFinder:
    """资源名称查找器"""
    
    def __init__(self, script: ScriptBase):
        """初始化查找器"""
        self.script = script
        self.results = []
        
    def validate_parameters(self) -> bool:
        """验证输入参数"""
        required_params = ['search_string', 'project_type']
        
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
    
    def find_files(self, directory: str, pattern: str) -> List[str]:
        """查找指定模式的文件"""
        files = []
        try:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if filename.endswith(pattern):
                        file_path = os.path.join(root, filename)
                        files.append(file_path)
        except Exception as e:
            self.script.error(f"遍历目录失败 {directory}: {e}")
        
        return files
    
    def search_in_config(self, content: str, search_string: str) -> List[Tuple[str, str]]:
        """在配置文件内容中搜索字符串"""
        results = []
        lines = content.splitlines()
        section = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('{'):
                section = line
            elif line.startswith('}'):
                section = ""
            elif search_string in line:
                results.append((section, line))
        
        return results
    
    def search_in_scripts(self, directory: str, search_string: str) -> List[Dict[str, Any]]:
        """在脚本文件中搜索字符串"""
        self.script.info("开始在脚本文件中搜索")
        
        pattern = ".cs"
        files = self.find_files(directory, pattern)
        results = []
        
        for file_path in files:
            try:
                content = self.read_file_with_chardet(file_path)
                if content and search_string in content:
                    results.append({
                        'type': 'script',
                        'filename': os.path.basename(file_path),
                        'filepath': file_path,
                        'matches': [f"包含字符串: {search_string}"]
                    })
            except Exception as e:
                self.script.warning(f"搜索脚本文件失败 {file_path}: {e}")
        
        return results
    
    def search_in_configs(self, directory: str, search_string: str) -> List[Dict[str, Any]]:
        """在配置文件中搜索字符串"""
        self.script.info("开始在配置文件中搜索")
        
        results = []
        
        try:
            for filename in os.listdir(directory):
                if filename.endswith('.txt'):
                    file_path = os.path.join(directory, filename)
                    content = self.read_file_with_chardet(file_path)
                    
                    if content is None:
                        continue
                    
                    hits = self.search_in_config(content, search_string)
                    if hits:
                        results.append({
                            'type': 'config',
                            'filename': filename,
                            'filepath': file_path,
                            'matches': [line for section, line in hits]
                        })
        except Exception as e:
            self.script.error(f"搜索配置文件失败 {directory}: {e}")
        
        return results
    
    def get_project_paths(self) -> Dict[str, str]:
        """获取项目路径配置"""
        project_type = self.script.get_parameter('project_type', 'domestic')
        
        # 这里需要根据实际情况配置路径
        # 暂时使用相对路径，实际使用时需要配置正确的路径
        if project_type == 'domestic':
            unity_root = self.script.get_parameter('domestic_path', 'D:\\fishdev')
        else:
            unity_root = self.script.get_parameter('global_path', 'D:\\fishglobal')
        
        return {
            'unity_root': unity_root,
            'config_path': os.path.join(unity_root, 'datapool', 'ElementData', 'BaseData'),
            'script_path': os.path.join(unity_root, 'client', 'MainProject')
        }
    
    def run_search(self) -> Dict[str, Any]:
        """执行搜索"""
        search_string = self.script.get_parameter('search_string')
        search_type = self.script.get_parameter('search_type', 'both')  # config, script, both
        
        paths = self.get_project_paths()
        results = {
            'search_string': search_string,
            'search_type': search_type,
            'config_results': [],
            'script_results': [],
            'total_matches': 0
        }
        
        # 搜索配置文件
        if search_type in ['config', 'both']:
            if os.path.exists(paths['config_path']):
                config_results = self.search_in_configs(paths['config_path'], search_string)
                results['config_results'] = config_results
                results['total_matches'] += len(config_results)
            else:
                self.script.warning(f"配置文件路径不存在: {paths['config_path']}")
        
        # 搜索脚本文件
        if search_type in ['script', 'both']:
            if os.path.exists(paths['script_path']):
                script_results = self.search_in_scripts(paths['script_path'], search_string)
                results['script_results'] = script_results
                results['total_matches'] += len(script_results)
            else:
                self.script.warning(f"脚本文件路径不存在: {paths['script_path']}")
        
        return results
    
    def generate_report(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成搜索报告"""
        self.script.info("生成搜索报告")
        
        report = {
            'summary': {
                'search_string': search_results['search_string'],
                'search_type': search_results['search_type'],
                'total_matches': search_results['total_matches'],
                'config_files_found': len(search_results['config_results']),
                'script_files_found': len(search_results['script_results'])
            },
            'config_results': search_results['config_results'],
            'script_results': search_results['script_results'],
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
                    message=f"搜索完成！找到 {search_results['total_matches']} 个匹配项",
                    data=report
                )
            else:
                return self.script.success_result(
                    message=f"未找到包含 '{search_results['search_string']}' 的文件",
                    data=report
                )
            
        except Exception as e:
            self.script.error(f"搜索执行失败: {e}")
            raise


def main_logic(script: ScriptBase) -> Dict[str, Any]:
    """主入口函数"""
    # 创建资源名称查找器实例
    finder = ResourceNameFinder(script)
    
    # 执行搜索
    return finder.run()


if __name__ == '__main__':
    # 使用模板创建脚本
    create_simple_script('find_resource_name', main_logic)