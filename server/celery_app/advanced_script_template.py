#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级脚本模板 - 支持多函数协作的复杂脚本开发
适用于需要多个函数协作的复杂业务逻辑

==========================================
📋 使用指南 - 重要：这不是直接使用的脚本！
==========================================

🎯 使用步骤：
1. 复制模板文件：
   cp server/celery_app/advanced_script_template.py server/celery_app/your_new_script.py

2. 修改脚本内容：
   a) 修改脚本名称和描述（文件开头注释）
   b) 修改必需参数列表（validate_parameters方法中的required_params）
   c) 修改数据处理逻辑（process_data方法中的业务逻辑）
   d) 修改主入口函数（文件末尾的create_simple_script调用）

3. 注册脚本：
   cd server
   python manage.py register_scripts

4. 配置按钮：
   在 server/myapp/management/commands/button_configs.json 中添加按钮配置
   然后运行：python manage.py setup_page_scripts

5. 重启服务：
   - 重启 Celery Worker
   - 重启 Django 服务器

🚀 两种使用方式：

方式1：使用高级脚本类（推荐用于复杂脚本）
- 适合需要多步骤处理、数据验证、报告生成的复杂业务逻辑
- 包含完整的验证、处理、报告流程
- 支持多步骤处理和数据验证

方式2：使用简单函数式编程（适合简单多函数脚本）
- 适合简单的多函数协作脚本
- 使用内部函数实现辅助逻辑
- 代码更简洁，适合快速开发

📝 关键修改点：
1. 脚本名称：修改 create_simple_script('your_script_name', main_logic) 中的脚本名称
2. 参数列表：修改 required_params 列表，添加您需要的参数
3. 业务逻辑：在 process_data 方法中实现您的具体业务逻辑
4. 验证逻辑：在 validate_results 方法中添加结果验证逻辑
5. 报告生成：在 generate_report 方法中自定义报告格式

⚠️ 重要提醒：
- 不要直接复制使用：这是一个模板，需要根据您的具体需求进行修改
- 必须注册脚本：修改完成后需要运行注册命令
- 必须配置按钮：需要在配置文件中添加按钮配置
- 必须重启服务：注册和配置后需要重启 Celery Worker 和 Django 服务器

==========================================
"""

import time
from typing import Dict, Any
from script_base import ScriptBase, create_simple_script


class AdvancedScript:
    """高级脚本类，支持多函数协作"""
    
    def __init__(self, script: ScriptBase):
        """初始化高级脚本"""
        self.script = script
        self.results = {}
        self.errors = []
        
    def validate_parameters(self) -> bool:
        """验证输入参数"""
        # 📝 修改点1：根据需要修改必需参数列表
        # 将下面的参数列表替换为您脚本实际需要的参数
        required_params = ['param1', 'param2']
        
        for param in required_params:
            if not self.script.get_parameter(param):
                self.script.error(f"缺少必需参数: {param}")
                return False
                
        self.script.info("参数验证通过")
        return True
    
    def initialize_data(self) -> Dict[str, Any]:
        """初始化数据"""
        self.script.info("开始初始化数据")
        
        # 📝 修改点2：根据您的参数需求修改数据初始化
        # 添加或删除参数，设置合适的默认值
        data = {
            'param1': self.script.get_parameter('param1'),
            'param2': self.script.get_parameter('param2'),
            'param3': self.script.get_parameter('param3', 'default_value'),
            'timestamp': time.time()
        }
        
        self.script.debug(f"初始化数据: {data}")
        return data
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据"""
        self.script.info("开始处理数据")
        
        try:
            # 📝 修改点3：在这里实现您的具体业务逻辑
            # 这是脚本的核心处理部分，请根据您的需求修改
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
        """验证处理结果"""
        self.script.info("开始验证结果")
        
        # 📝 修改点4：添加您的结果验证逻辑
        # 根据您的业务需求添加验证条件
        if not data.get('processed_param1'):
            self.script.error("处理结果验证失败: processed_param1 为空")
            return False
            
        if data.get('calculated_value', 0) <= 0:
            self.script.warning("计算值可能异常")
            
        self.script.info("结果验证通过")
        return True
    
    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告"""
        self.script.info("开始生成报告")
        
        # 📝 修改点5：自定义报告格式
        # 根据您的需求修改报告结构和内容
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
        
        # 📝 修改点6：添加资源清理逻辑（可选）
        # 如果需要清理临时文件、关闭连接等，在这里添加
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
    """主入口函数 - 使用高级脚本类"""
    # 创建高级脚本实例
    advanced_script = AdvancedScript(script)
    
    # 执行脚本
    return advanced_script.run()


# 🚀 方式2：简单函数式编程方式（适合简单多函数脚本）
def simple_main_logic(script: ScriptBase) -> Dict[str, Any]:
    """简单主逻辑函数 - 适合简单的多函数脚本"""
    
    # 📝 修改点：根据您的需求添加或修改辅助函数
    def helper_function1(param):
        """辅助函数1 - 请根据您的业务需求修改"""
        script.debug(f"辅助函数1处理: {param}")
        return param.upper() if isinstance(param, str) else str(param)
    
    def helper_function2(param):
        """辅助函数2 - 请根据您的业务需求修改"""
        script.debug(f"辅助函数2处理: {param}")
        return param * 2 if isinstance(param, (int, float)) else 0
    
    # 主逻辑
    script.info("开始执行简单多函数逻辑")
    
    try:
        # 📝 修改点：根据您的参数需求修改参数获取
        # 获取参数
        param1 = script.get_parameter('param1', 'test')
        param2 = script.get_parameter('param2', 10)
        
        # 📝 修改点：根据您的业务逻辑修改函数调用
        # 调用辅助函数
        result1 = helper_function1(param1)
        result2 = helper_function2(param2)
        
        # 📝 修改点：根据您的需求修改结果数据结构
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
    # 📝 修改点7：修改脚本名称（必须）
    # 将 'advanced_script' 替换为您的新脚本名称
    # 选择执行方式：
    # 方式1：使用高级脚本类（推荐用于复杂脚本）
    create_simple_script('advanced_script', main_logic)
    
    # 方式2：使用简单函数式编程（适合简单多函数脚本）
    # create_simple_script('simple_multi_function_script', simple_main_logic)