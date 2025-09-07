#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本配置管理器
负责加载和管理脚本参数配置
"""

import json
import os
from typing import Dict, List, Any, Optional
from django.conf import settings


class ScriptConfigManager:
    """脚本配置管理器"""
    
    def __init__(self):
        self.config_file = os.path.join(
            settings.BASE_DIR, 
            'myapp', 
            'management', 
            'commands', 
            'script_configs.json'
        )
        self._config_cache = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
            else:
                self._config_cache = {}
        except Exception as e:
            print(f"加载脚本配置文件失败: {e}")
            self._config_cache = {}
    
    def reload_config(self):
        """重新加载配置"""
        self._config_cache = None
        self._load_config()
    
    def get_script_config(self, script_name: str) -> List[Dict[str, Any]]:
        """获取指定脚本的参数配置"""
        if not self._config_cache:
            return []
        
        # 支持带.py后缀和不带后缀的脚本名
        script_key = script_name
        if not script_key.endswith('.py'):
            script_key += '.py'
        
        return self._config_cache.get(script_key, [])
    
    def get_all_scripts(self) -> List[str]:
        """获取所有配置的脚本名称"""
        if not self._config_cache:
            return []
        return list(self._config_cache.keys())
    
    def validate_parameters(self, script_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证脚本参数"""
        config = self.get_script_config(script_name)
        if not config:
            return {'valid': True, 'errors': [], 'processed_params': parameters}
        
        errors = []
        processed_params = {}
        
        # 创建配置字典便于查找
        config_dict = {param['name']: param for param in config}
        
        # 验证必填参数
        for param_config in config:
            param_name = param_config['name']
            is_required = param_config.get('required', False)
            default_value = param_config.get('default')
            
            if param_name in parameters:
                # 参数存在，进行类型和值验证
                value = parameters[param_name]
                validated_value, error = self._validate_parameter_value(param_config, value)
                
                if error:
                    errors.append(f"参数 '{param_name}': {error}")
                else:
                    processed_params[param_name] = validated_value
            elif is_required:
                # 必填参数缺失
                errors.append(f"缺少必填参数: '{param_name}'")
            elif default_value is not None:
                # 使用默认值
                processed_params[param_name] = default_value
        
        # 检查是否有未定义的参数
        for param_name in parameters:
            if param_name not in config_dict:
                errors.append(f"未定义的参数: '{param_name}'")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'processed_params': processed_params
        }
    
    def _validate_parameter_value(self, param_config: Dict[str, Any], value: Any) -> tuple:
        """验证单个参数值"""
        param_type = param_config.get('type', 'text')
        param_name = param_config.get('name', 'unknown')
        
        try:
            if param_type == 'text':
                return str(value), None
            
            elif param_type == 'number':
                num_value = float(value) if '.' in str(value) else int(value)
                
                # 检查范围
                min_val = param_config.get('min')
                max_val = param_config.get('max')
                
                if min_val is not None and num_value < min_val:
                    return None, f"值不能小于 {min_val}"
                if max_val is not None and num_value > max_val:
                    return None, f"值不能大于 {max_val}"
                
                return num_value, None
            
            elif param_type == 'switch':
                if isinstance(value, bool):
                    return value, None
                elif isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on'), None
                else:
                    return bool(value), None
            
            elif param_type == 'select':
                options = param_config.get('options', [])
                if options and value not in options:
                    return None, f"值必须是以下选项之一: {', '.join(map(str, options))}"
                return value, None
            
            elif param_type == 'checkbox':
                multiple = param_config.get('multiple', False)
                options = param_config.get('options', [])
                
                if multiple:
                    if not isinstance(value, list):
                        value = [value] if value else []
                    
                    # 验证每个选项
                    if options:
                        invalid_options = [v for v in value if v not in options]
                        if invalid_options:
                            return None, f"无效的选项: {', '.join(invalid_options)}"
                    
                    return value, None
                else:
                    if options and value not in options:
                        return None, f"值必须是以下选项之一: {', '.join(map(str, options))}"
                    return value, None
            
            else:
                return value, None
                
        except (ValueError, TypeError) as e:
            return None, f"类型转换错误: {str(e)}"
    
    def get_parameter_schema(self, script_name: str) -> Dict[str, Any]:
        """获取参数模式定义，用于前端渲染"""
        config = self.get_script_config(script_name)
        
        schema = {
            'script_name': script_name,
            'parameters': config,
            'form_layout': self._generate_form_layout(config)
        }
        
        return schema
    
    def _generate_form_layout(self, config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成表单布局信息"""
        layout = {
            'sections': [],
            'validation_rules': {}
        }
        
        # 简单的单节布局
        if config:
            section = {
                'title': '参数配置',
                'fields': []
            }
            
            for param_config in config:
                param_name = param_config['name']
                field_info = {
                    'name': param_name,
                    'label': param_config.get('label', param_name),
                    'type': param_config.get('type', 'text'),
                    'required': param_config.get('required', False),
                    'default': param_config.get('default'),
                    'placeholder': param_config.get('placeholder', ''),
                    'options': param_config.get('options', []),
                    'multiple': param_config.get('multiple', False),
                    'min': param_config.get('min'),
                    'max': param_config.get('max')
                }
                
                section['fields'].append(field_info)
                
                # 生成验证规则
                if param_config.get('required'):
                    layout['validation_rules'][param_name] = {
                        'required': True,
                        'message': f"{param_config.get('label', param_name)} 是必填项"
                    }
            
            layout['sections'].append(section)
        
        return layout


# 全局配置管理器实例
script_config_manager = ScriptConfigManager()
