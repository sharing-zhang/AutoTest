#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级脚本模板 - 支持多函数的复杂脚本开发
适用于需要多个函数协作的复杂业务逻辑
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional
from script_base import ScriptBase, create_simple_script


class AdvancedScript:
    """高级脚本类，支持多函数协作"""
    
    def __init__(self, script: ScriptBase):
        """
        初始化高级脚本
        
        Args:
            script: ScriptBase实例，提供基础功能
        """
        self.script = script
        self.results = {}
        self.errors = []
        
    def validate_parameters(self) -> bool:
        """
        验证输入参数
        
        Returns:
            bool: 验证是否通过
        """
        # 获取必需参数
        required_params = ['param1', 'param2']  # 根据需要修改
        optional_params = ['param3', 'param4']  # 根据需要修改
        
        # 检查必需参数
        for param in required_params:
            if not self.script.get_parameter(param):
                self.script.error(f"缺少必需参数: {param}")
                return False
                
        self.script.info("参数验证通过")
        return True
    
    def initialize_data(self) -> Dict[str, Any]:
        """
        初始化数据
        
        Returns:
            Dict[str, Any]: 初始化后的数据
        """
        self.script.info("开始初始化数据")
        
        data = {
            'param1': self.script.get_parameter('param1'),
            'param2': self.script.get_parameter('param2'),
            'param3': self.script.get_parameter('param3', 'default_value'),
            'timestamp': time.time()
        }
        
        self.script.debug(f"初始化数据: {data}")
        return data
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 处理后的数据
        """
        self.script.info("开始处理数据")
        
        try:
            # 数据处理逻辑
            processed_data = data.copy()
            processed_data['processed_param1'] = str(data['param1']).upper()
            processed_data['calculated_value'] = data['param2'] * 2
            processed_data['processing_time'] = time.time()
            
            self.script.debug(f"数据处理完成: {processed_data}")
            return processed_data
            
        except Exception as e:
            self.script.error(f"数据处理失败: {e}")
            raise
    
    def validate_results(self, data: Dict[str, Any]) -> bool:
        """
        验证处理结果
        
        Args:
            data: 处理后的数据
            
        Returns:
            bool: 验证是否通过
        """
        self.script.info("开始验证结果")
        
        # 验证逻辑
        if not data.get('processed_param1'):
            self.script.error("处理结果验证失败: processed_param1 为空")
            return False
            
        if data.get('calculated_value', 0) <= 0:
            self.script.warning("计算值可能异常")
            
        self.script.info("结果验证通过")
        return True
    
    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成报告
        
        Args:
            data: 处理后的数据
            
        Returns:
            Dict[str, Any]: 生成的报告
        """
        self.script.info("开始生成报告")
        
        report = {
            'summary': {
                'total_items': len(data),
                'processing_time': data.get('processing_time', 0),
                'status': 'completed'
            },
            'details': data,
            'metadata': {
                'script_name': self.script.script_name,
                'execution_time': time.time(),
                'version': '1.0.0'
            }
        }
        
        self.script.debug(f"报告生成完成: {report}")
        return report
    
    def cleanup(self):
        """清理资源"""
        self.script.info("开始清理资源")
        # 清理逻辑
        self.script.info("资源清理完成")
    
    def run(self) -> Dict[str, Any]:
        """
        执行完整的脚本流程
        
        Returns:
            Dict[str, Any]: 执行结果
        """
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
            
            # 7. 返回成功结果
            return self.script.success_result(
                message="高级脚本执行成功！",
                data=report
            )
            
        except Exception as e:
            self.script.error(f"脚本执行失败: {e}")
            # 确保清理资源
            try:
                self.cleanup()
            except:
                pass
            raise


def main_logic(script: ScriptBase) -> Dict[str, Any]:
    """
    主入口函数 - 使用高级脚本类
    
    Args:
        script: ScriptBase实例
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    # 创建高级脚本实例
    advanced_script = AdvancedScript(script)
    
    # 执行脚本
    return advanced_script.run()


# 可选：直接函数式编程方式
def simple_main_logic(script: ScriptBase) -> Dict[str, Any]:
    """
    简单主逻辑函数 - 适合简单的多函数脚本
    
    Args:
        script: ScriptBase实例
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    def helper_function1(param):
        """辅助函数1"""
        script.debug(f"辅助函数1处理: {param}")
        return param.upper() if isinstance(param, str) else str(param)
    
    def helper_function2(param):
        """辅助函数2"""
        script.debug(f"辅助函数2处理: {param}")
        return param * 2 if isinstance(param, (int, float)) else 0
    
    # 主逻辑
    script.info("开始执行简单多函数逻辑")
    
    try:
        # 获取参数
        param1 = script.get_parameter('param1', 'test')
        param2 = script.get_parameter('param2', 10)
        
        # 调用辅助函数
        result1 = helper_function1(param1)
        result2 = helper_function2(param2)
        
        # 组合结果
        result_data = {
            'original_param1': param1,
            'original_param2': param2,
            'processed_param1': result1,
            'processed_param2': result2,
            'combined_result': f"{result1}_{result2}"
        }
        
        script.info("简单多函数逻辑执行完成")
        
        return script.success_result(
            message="简单多函数脚本执行成功！",
            data=result_data
        )
        
    except Exception as e:
        script.error(f"简单多函数逻辑执行失败: {e}")
        raise


if __name__ == '__main__':
    # 选择执行方式：
    # 方式1：使用高级脚本类（推荐用于复杂脚本）
    create_simple_script('advanced_script', main_logic)
    
    # 方式2：使用简单函数式编程（适合简单多函数脚本）
    # create_simple_script('simple_multi_function_script', simple_main_logic)
