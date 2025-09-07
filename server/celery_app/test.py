#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 用于验证脚本系统功能
"""

from script_base import create_simple_script

def main_logic(script):
    """
    主要业务逻辑函数 - 输出固定文本
    
    Args:
        script: ScriptBase实例，提供以下方法：
            - script.debug(message): 输出调试信息
            - script.info(message): 输出普通信息
            - script.warning(message): 输出警告信息
            - script.error(message): 输出错误信息
            - script.success_result(message, data): 创建成功结果
            - script.error_result(message, error_type): 创建错误结果
    """
    
    script.info("开始执行不需要传参的脚本")
    
    try:
        # 输出指定的文本
        output_text = "不需要传参的脚本"
        
        script.info(f"输出文本: {output_text}")
        
        # 返回成功结果
        return script.success_result(
            message=output_text,
            data={
                'output_text': output_text,
                'script_type': 'no_parameters',
                'execution_time': script.start_time
            }
        )
        
    except Exception as e:
        # 错误处理
        script.error(f"脚本执行失败: {e}")
        raise  # 重新抛出异常让ScriptBase处理

if __name__ == '__main__':
    # 使用测试脚本名称
    create_simple_script('test_script', main_logic)