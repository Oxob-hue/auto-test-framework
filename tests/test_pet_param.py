"""接口参数化用例：JSON 数据驱动创建宠物。

数据文件统一放到 test_data/ 并通过项目根目录定位，与执行命令所在目录解耦。
"""
import json

import allure
import pytest

from api.pet_api import PetApi
from common.config_util import PROJECT_ROOT
from common.logger import get_logger

logger = get_logger("test_pet_param")

pytestmark = [
    pytest.mark.api,
    allure.epic("接口自动化"),
    allure.feature("宠物创建-数据驱动"),
]

_DATA_FILE = PROJECT_ROOT / "test_data" / "pet_data.json"


def _load_pet_cases() -> list:
    """从 JSON 测试数据文件读取参数化用例。"""
    with open(_DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["create_pets"]


CASES = _load_pet_cases()


def _delete_quietly(pet_api: PetApi, pet_id: int) -> None:
    pet_api.delete_pet(pet_id)


@allure.story("JSON 数据驱动创建宠物")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("case", CASES, ids=[case["pet_name"] for case in CASES])
def test_create_pet_from_json(pet_api: PetApi, case: dict):
    """使用 JSON 中的多组数据创建宠物，校验名称与状态。"""
    pet_id = case["pet_id"]
    _, resp = pet_api.create_pet(pet_id=pet_id, name=case["pet_name"], status=case["status"])
    try:
        with allure.step(f"按 JSON 数据创建宠物 pet_id={pet_id}"):
            assert resp.status_code == 200, f"创建宠物失败: {resp.status_code} {resp.text[:200]}"
        with allure.step("断言返回体与数据一致"):
            body = resp.json()
            assert body["id"] == pet_id
            assert body["name"] == case["pet_name"]
            assert body["status"] == case["status"]
        logger.info("JSON 数据驱动创建成功: %s", case)
    finally:
        _delete_quietly(pet_api, pet_id)
