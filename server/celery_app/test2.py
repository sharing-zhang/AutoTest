#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本--文件扫描器脚本
功能：扫描指定目录下的文件，支持按后缀名过滤、递归扫描等选项
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from script_base import ScriptBase, create_simple_script


def scan_files(script: ScriptBase) -> Dict[str, Any]:
    """文件扫描主逻辑"""
    
    # 获取参数
    directory = script.get_parameter('directory', 'C:\\temp')
    file_extensions = script.get_parameter('file_extensions', ['.txt', '.log'])
    recursive = script.get_parameter('recursive', True)
    max_depth = script.get_parameter('max_depth', 3)
    include_hidden = script.get_parameter('include_hidden', False)
    output_format = script.get_parameter('output_format', 'list')
    
    script.info(f"开始扫描目录: {directory}")
    script.info(f"文件扩展名: {file_extensions}")
    script.info(f"递归扫描: {recursive}, 最大深度: {max_depth}")
    script.info(f"包含隐藏文件: {include_hidden}")
    script.info(f"输出格式: {output_format}")
    
    # 验证目录是否存在
    if not os.path.exists(directory):
        return script.error_result(f"目录不存在: {directory}", "DirectoryNotFound")
    
    if not os.path.isdir(directory):
        return script.error_result(f"路径不是目录: {directory}", "NotADirectory")
    
    # 开始扫描
    start_time = time.time()
    scanned_files = []
    total_size = 0
    error_count = 0
    
    try:
        for file_info in scan_directory(
            directory, 
            file_extensions, 
            recursive, 
            max_depth, 
            include_hidden
        ):
            scanned_files.append(file_info)
            total_size += file_info.get('size', 0)
            
    except Exception as e:
        error_count += 1
        script.warning(f"扫描过程中出现错误: {e}")
    
    scan_duration = time.time() - start_time
    
    script.info(f"扫描完成，共找到 {len(scanned_files)} 个文件")
    script.info(f"总大小: {format_file_size(total_size)}")
    script.info(f"扫描耗时: {scan_duration:.2f} 秒")
    
    # 根据输出格式组织结果
    if output_format == 'detailed':
        result_data = format_detailed_output(scanned_files, directory)
    elif output_format == 'tree':
        result_data = format_tree_output(scanned_files, directory)
    else:  # list
        result_data = format_list_output(scanned_files)
    
    # 添加统计信息
    result_data['statistics'] = {
        'total_files': len(scanned_files),
        'total_size': total_size,
        'total_size_formatted': format_file_size(total_size),
        'scan_duration': round(scan_duration, 2),
        'error_count': error_count,
        'scanned_directory': directory,
        'extensions_filter': file_extensions,
        'scan_options': {
            'recursive': recursive,
            'max_depth': max_depth,
            'include_hidden': include_hidden
        }
    }
    
    return script.success_result(
        f"成功扫描 {directory}，找到 {len(scanned_files)} 个文件",
        result_data
    )


def scan_directory(
    directory: str, 
    extensions: List[str], 
    recursive: bool = True, 
    max_depth: int = 3, 
    include_hidden: bool = False,
    current_depth: int = 0
) -> List[Dict[str, Any]]:
    """递归扫描目录"""
    
    files = []
    
    try:
        # 检查深度限制
        if max_depth > 0 and current_depth >= max_depth:
            return files
        
        directory_path = Path(directory)
        
        for item in directory_path.iterdir():
            try:
                # 跳过隐藏文件/目录（如果设置不包含）
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                if item.is_file():
                    # 检查文件扩展名
                    if not extensions or item.suffix.lower() in [ext.lower() for ext in extensions]:
                        file_info = get_file_info(item)
                        files.append(file_info)
                        
                elif item.is_dir() and recursive:
                    # 递归扫描子目录
                    subdir_files = scan_directory(
                        str(item), 
                        extensions, 
                        recursive, 
                        max_depth, 
                        include_hidden,
                        current_depth + 1
                    )
                    files.extend(subdir_files)
                    
            except (PermissionError, OSError) as e:
                # 跳过无权限访问的文件/目录
                continue
                
    except (PermissionError, OSError) as e:
        # 跳过无权限访问的目录
        pass
    
    return files


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """获取文件详细信息"""
    try:
        stat_info = file_path.stat()
        
        return {
            'name': file_path.name,
            'path': str(file_path),
            'relative_path': str(file_path.relative_to(file_path.anchor)) if file_path.is_absolute() else str(file_path),
            'size': stat_info.st_size,
            'size_formatted': format_file_size(stat_info.st_size),
            'extension': file_path.suffix,
            'created_time': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            'accessed_time': datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            'is_readonly': not (stat_info.st_mode & 0o200),
            'parent_directory': str(file_path.parent)
        }
    except (OSError, ValueError) as e:
        return {
            'name': file_path.name,
            'path': str(file_path),
            'error': str(e)
        }


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def format_list_output(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """格式化为简单列表输出"""
    return {
        'format': 'list',
        'files': [
            {
                'name': f['name'],
                'path': f['path'],
                'size': f.get('size_formatted', 'Unknown'),
                'modified': f.get('modified_time', 'Unknown')
            }
            for f in files
        ]
    }


def format_detailed_output(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """格式化为详细信息输出"""
    return {
        'format': 'detailed',
        'files': files,
        'summary_by_extension': get_extension_summary(files)
    }


def format_tree_output(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """格式化为树状结构输出"""
    tree = {}
    
    for file_info in files:
        path_parts = Path(file_info['path']).parts
        current_level = tree
        
        # 构建目录树
        for part in path_parts[:-1]:  # 除了文件名的所有部分
            if part not in current_level:
                current_level[part] = {'dirs': {}, 'files': []}
            current_level = current_level[part]['dirs']
        
        # 添加文件到最后一级目录
        parent_dir = path_parts[-2] if len(path_parts) > 1 else 'root'
        if parent_dir not in current_level:
            current_level[parent_dir] = {'dirs': {}, 'files': []}
        
        current_level[parent_dir]['files'].append({
            'name': file_info['name'],
            'size': file_info.get('size_formatted', 'Unknown'),
            'modified': file_info.get('modified_time', 'Unknown')
        })
    
    return {
        'format': 'tree',
        'tree': tree,
        'files_count': len(files)
    }


def get_extension_summary(files: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """按扩展名分组统计"""
    summary = {}
    
    for file_info in files:
        ext = file_info.get('extension', 'no_extension')
        if not ext:
            ext = 'no_extension'
        
        if ext not in summary:
            summary[ext] = {
                'count': 0,
                'total_size': 0,
                'files': []
            }
        
        summary[ext]['count'] += 1
        summary[ext]['total_size'] += file_info.get('size', 0)
        summary[ext]['files'].append(file_info['name'])
    
    # 添加格式化的大小
    for ext_data in summary.values():
        ext_data['total_size_formatted'] = format_file_size(ext_data['total_size'])
    
    return summary


if __name__ == '__main__':
    create_simple_script('file_scanner', scan_files)
