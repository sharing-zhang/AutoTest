#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本模板 - 复制此文件开始开发新脚本
支持单函数和多函数场景
请修改脚本名称、描述和业务逻辑
"""

from script_base import create_simple_script

# ==================== 辅助函数区域 ====================
def helper_function1(script, param):
    """
    辅助函数1 - 处理特定逻辑
    
    Args:
        script: ScriptBase实例
        param: 输入参数
        
    Returns:
        处理后的结果
    """
    script.debug(f"辅助函数1处理参数: {param}")
    # TODO: 添加你的处理逻辑
    return param.upper() if isinstance(param, str) else str(param)

def helper_function2(script, param):
    """
    辅助函数2 - 处理特定逻辑
    
    Args:
        script: ScriptBase实例
        param: 输入参数
        
    Returns:
        处理后的结果
    """
    script.debug(f"辅助函数2处理参数: {param}")
    # TODO: 添加你的处理逻辑
    return param * 2 if isinstance(param, (int, float)) else 0

def validate_data(script, data):
    """
    数据验证函数
    
    Args:
        script: ScriptBase实例
        data: 要验证的数据
        
    Returns:
        bool: 验证是否通过
    """
    script.debug("开始验证数据")
    # TODO: 添加验证逻辑
    return True

# ==================== 主逻辑函数 ====================
def main_logic(script):
    """
    主要业务逻辑函数
    
    Args:
        script: ScriptBase实例，提供以下方法：
            - script.get_parameter(key, default): 获取参数
            - script.debug(message): 输出调试信息
            - script.info(message): 输出普通信息
            - script.warning(message): 输出警告信息
            - script.error(message): 输出错误信息
            - script.success_result(message, data): 创建成功结果
            - script.error_result(message, error_type): 创建错误结果
    """
    
    # 1. 获取参数
    param1 = script.get_parameter('param1', 'default_value')
    param2 = script.get_parameter('param2', 100)
    
    script.info("脚本开始执行主要逻辑")
    script.debug(f"参数1: {param1}, 参数2: {param2}")
    
    # 2. 执行你的业务逻辑
    try:
        # 调用辅助函数处理数据
        processed_param1 = helper_function1(script, param1)
        processed_param2 = helper_function2(script, param2)
        
        # 组合结果数据
        result_data = {
            'original_param1': param1,
            'original_param2': param2,
            'processed_param1': processed_param1,
            'processed_param2': processed_param2,
            'status': 'completed'
        }
        
        # 验证结果
        if not validate_data(script, result_data):
            return script.error_result("数据验证失败", "ValidationError")
        
        script.info("业务逻辑执行完成")
        
        # 3. 返回成功结果
        return script.success_result(
            message="脚本执行成功！",  # 这个消息会在前端显示
            data=result_data  # 附加数据
        )
        
    except Exception as e:
        # 4. 错误处理（可选，ScriptBase会自动处理）
        script.error(f"业务逻辑执行失败: {e}")
        raise  # 重新抛出异常让ScriptBase处理

# ==================== 简单单函数版本（可选）====================
def simple_main_logic(script):
    """
    简单主逻辑函数 - 适合单一功能脚本
    
    Args:
        script: ScriptBase实例
    """
    # 获取参数
    param1 = script.get_parameter('param1', 'default_value')
    param2 = script.get_parameter('param2', 100)
    
    script.info("简单脚本开始执行")
    
    try:
        # 简单的业务逻辑
        result_data = {
            'processed_param1': param1.upper() if isinstance(param1, str) else param1,
            'calculated_value': param2 * 2,
            'status': 'completed'
        }
        
        return script.success_result(
            message="简单脚本执行成功！",
            data=result_data
        )
        
    except Exception as e:
        script.error(f"简单脚本执行失败: {e}")
        raise

if __name__ == '__main__':
    # 选择执行方式：
    # 方式1：多函数版本（推荐用于复杂逻辑）
    create_simple_script('your_script_name', main_logic)
    
    # 方式2：简单单函数版本（适合简单逻辑）
    # create_simple_script('your_simple_script_name', simple_main_logic)
