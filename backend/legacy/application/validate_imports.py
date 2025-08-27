#!/usr/bin/env python3
"""
应用层导入规范验证脚本
======================

用于检查应用层文件是否遵循统一的导入规范。

使用方法:
    python validate_imports.py
    python validate_imports.py --file specific_file.py
    python validate_imports.py --fix  # 自动修复导入顺序
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 导入规范常量
IMPORT_SECTIONS = [
    "# 标准库导入",
    "# 第三方库导入", 
    "# 核心层导入",
    "# 领域层导入",
    "# 基础设施层导入",
    "# 应用层内部导入"
]

STANDARD_LIBRARY_MODULES = {
    'abc', 'asyncio', 'collections', 'dataclasses', 'datetime', 'enum', 
    'functools', 'itertools', 'json', 'logging', 'os', 'pathlib', 're', 
    'sys', 'typing', 'uuid', '__future__'
}

THIRD_PARTY_MODULES = {
    'fastapi', 'pydantic', 'sqlalchemy', 'psutil', 'pytest', 'requests'
}


class ImportValidator:
    """导入规范验证器"""
    
    def __init__(self):
        self.application_dir = Path(__file__).parent
        self.issues = []
    
    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """验证单个文件的导入规范"""
        if not file_path.exists() or file_path.suffix != '.py':
            return {"valid": False, "error": "文件不存在或不是Python文件"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            imports = self._extract_imports(content)
            issues = self._check_import_order(imports, file_path)
            
            return {
                "file": str(file_path),
                "valid": len(issues) == 0,
                "issues": issues,
                "imports": imports
            }
            
        except Exception as e:
            return {"valid": False, "error": f"读取文件失败: {e}"}
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """提取文件中的导入语句"""
        imports = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')) and not stripped.startswith('#'):
                import_type = self._classify_import(stripped)
                imports.append({
                    "line_number": i + 1,
                    "content": stripped,
                    "type": import_type,
                    "raw_line": line
                })
        
        return imports
    
    def _classify_import(self, import_line: str) -> str:
        """分类导入语句"""
        if import_line.startswith('from __future__'):
            return "标准库"
        
        # 提取模块名
        if import_line.startswith('import '):
            module = import_line.split()[1].split('.')[0]
        elif import_line.startswith('from '):
            module_part = import_line.split()[1]
            if module_part.startswith('.'):
                # 相对导入
                if module_part.startswith('...core'):
                    return "核心层"
                elif module_part.startswith('...domain'):
                    return "领域层"
                elif module_part.startswith('...infrastructure'):
                    return "基础设施层"
                elif module_part.startswith('.'):
                    return "应用层内部"
                else:
                    return "未知"
            else:
                module = module_part.split('.')[0]
        else:
            return "未知"
        
        # 分类模块
        if module in STANDARD_LIBRARY_MODULES:
            return "标准库"
        elif module in THIRD_PARTY_MODULES:
            return "第三方库"
        else:
            return "第三方库"  # 默认归类为第三方库
    
    def _check_import_order(self, imports: List[Dict[str, Any]], file_path: Path) -> List[str]:
        """检查导入顺序"""
        issues = []
        
        if not imports:
            return issues
        
        # 期望的导入顺序
        expected_order = ["标准库", "第三方库", "核心层", "领域层", "基础设施层", "应用层内部"]
        
        # 检查导入分组
        current_group = None
        group_order = []
        
        for imp in imports:
            import_type = imp["type"]
            if import_type != current_group:
                current_group = import_type
                group_order.append(import_type)
        
        # 检查顺序是否正确
        filtered_expected = [t for t in expected_order if t in group_order]
        
        if group_order != filtered_expected:
            issues.append(
                f"导入顺序不正确。当前顺序: {group_order}, 期望顺序: {filtered_expected}"
            )
        
        # 检查是否有导入分组注释
        content_lines = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content_lines = f.readlines()
        except:
            pass
        
        has_section_comments = any(
            line.strip() in IMPORT_SECTIONS 
            for line in content_lines
        )
        
        if not has_section_comments and len(group_order) > 1:
            issues.append("缺少导入分组注释")
        
        return issues
    
    def validate_directory(self, directory: Path = None) -> Dict[str, Any]:
        """验证整个目录的导入规范"""
        if directory is None:
            directory = self.application_dir
        
        results = []
        total_files = 0
        valid_files = 0
        
        for py_file in directory.rglob("*.py"):
            if py_file.name == '__init__.py' or py_file.name == 'validate_imports.py':
                continue
            
            total_files += 1
            result = self.validate_file(py_file)
            results.append(result)
            
            if result.get("valid", False):
                valid_files += 1
        
        return {
            "total_files": total_files,
            "valid_files": valid_files,
            "invalid_files": total_files - valid_files,
            "results": results,
            "compliance_rate": (valid_files / total_files * 100) if total_files > 0 else 0
        }
    
    def generate_report(self, validation_result: Dict[str, Any]) -> str:
        """生成验证报告"""
        report = []
        report.append("=" * 60)
        report.append("应用层导入规范验证报告")
        report.append("=" * 60)
        report.append("")
        
        # 总体统计
        total = validation_result["total_files"]
        valid = validation_result["valid_files"]
        invalid = validation_result["invalid_files"]
        compliance = validation_result["compliance_rate"]
        
        report.append(f"总文件数: {total}")
        report.append(f"符合规范: {valid}")
        report.append(f"不符合规范: {invalid}")
        report.append(f"合规率: {compliance:.1f}%")
        report.append("")
        
        # 详细结果
        if invalid > 0:
            report.append("不符合规范的文件:")
            report.append("-" * 40)
            
            for result in validation_result["results"]:
                if not result.get("valid", False):
                    file_path = result["file"]
                    report.append(f"\n📁 {file_path}")
                    
                    if "error" in result:
                        report.append(f"   ❌ {result['error']}")
                    else:
                        for issue in result.get("issues", []):
                            report.append(f"   ⚠️  {issue}")
        else:
            report.append("🎉 所有文件都符合导入规范!")
        
        return "\n".join(report)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="验证应用层导入规范")
    parser.add_argument("--file", help="验证指定文件")
    parser.add_argument("--directory", help="验证指定目录")
    parser.add_argument("--report", action="store_true", help="生成详细报告")
    
    args = parser.parse_args()
    
    validator = ImportValidator()
    
    if args.file:
        # 验证单个文件
        file_path = Path(args.file)
        result = validator.validate_file(file_path)
        
        print(f"验证文件: {file_path}")
        if result["valid"]:
            print("✅ 导入规范符合要求")
        else:
            print("❌ 导入规范不符合要求")
            if "error" in result:
                print(f"错误: {result['error']}")
            else:
                for issue in result.get("issues", []):
                    print(f"  - {issue}")
    
    elif args.directory:
        # 验证指定目录
        directory = Path(args.directory)
        validation_result = validator.validate_directory(directory)
        
        if args.report:
            print(validator.generate_report(validation_result))
        else:
            compliance = validation_result["compliance_rate"]
            total = validation_result["total_files"]
            valid = validation_result["valid_files"]
            print(f"验证完成: {valid}/{total} 文件符合规范 ({compliance:.1f}%)")
    
    else:
        # 验证当前应用层目录
        validation_result = validator.validate_directory()
        
        if args.report:
            print(validator.generate_report(validation_result))
        else:
            compliance = validation_result["compliance_rate"]
            total = validation_result["total_files"]
            valid = validation_result["valid_files"]
            print(f"应用层导入规范验证完成: {valid}/{total} 文件符合规范 ({compliance:.1f}%)")


if __name__ == "__main__":
    main()
