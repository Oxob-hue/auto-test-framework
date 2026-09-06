"""基于 jsonschema 的接口响应结构校验工具。

用途：在“字段存在”这类浅层断言之外，进一步约束响应结构（字段类型 / 必填项 /
枚举取值范围），防止前后端字段悄悄漂移而用例仍然通过。
"""
import json
from typing import Any

from jsonschema import validate

from common.config_util import PROJECT_ROOT


def load_schema(relative_path: str) -> dict:
    """读取 schema 文件（路径基于项目根目录，如 test_data/pet_response_schema.json）。"""
    with open(PROJECT_ROOT / relative_path, encoding="utf-8") as f:
        return json.load(f)


def validate_response(instance: Any, schema_relative_path: str) -> None:
    """按 schema 校验响应结构；不满足时抛出 ValidationError（等价于用例失败）。

    Args:
        instance: 待校验对象（如 resp.json()）
        schema_relative_path: schema 文件相对项目根目录的路径
    """
    schema = load_schema(schema_relative_path)
    validate(instance, schema)
