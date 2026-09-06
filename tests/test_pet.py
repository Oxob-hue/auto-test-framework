"""Petstore 宠物管理接口用例：覆盖增删改查主流程与查询异常场景。"""
import allure
import pytest

from api.pet_api import PetApi
from common.json_schema_util import validate_response

pytestmark = [
    pytest.mark.api,
    allure.epic("接口自动化"),
    allure.feature("Petstore 宠物管理"),
]

# 宠物对象响应结构约束文件（相对项目根目录）
PET_SCHEMA = "test_data/pet_response_schema.json"


def _delete_quietly(pet_api: PetApi, pet_id: int) -> None:
    """尽力清理测试数据（幂等），避免失败用例残留脏数据。"""
    pet_api.delete_pet(pet_id)


def _assert_pet_body(body: dict, pet_id: int, name: str, status: str) -> None:
    """字段级断言 + 结构约束（schema）双重校验。"""
    validate_response(body, PET_SCHEMA)
    assert body["id"] == pet_id, "返回 ID 与请求不一致"
    assert body["name"] == name, f"返回名称与预期不一致: {body['name']}"
    assert body["status"] == status, f"返回状态与预期不一致: {body['status']}"


# ---------------------------------------------------------------- 查询
@allure.story("按 ID 查询")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_pet_by_id(created_pet_id: int, pet_api: PetApi):
    """正向：查询已创建的宠物应返回 200，且字段与创建时一致。"""
    with allure.step("GET /pet/{id} 查询宠物"):
        resp = pet_api.get_pet(created_pet_id)
    with allure.step("断言状态码为 200"):
        assert resp.status_code == 200, f"查询宠物失败: {resp.status_code} {resp.text[:200]}"
    with allure.step("断言返回字段与结构约束"):
        body = resp.json()
        _assert_pet_body(body, created_pet_id, "fixture_doggie", "available")


@allure.story("查询异常场景")
@pytest.mark.negative
def test_get_non_exist_pet(pet_api: PetApi):
    """反向：查询不存在的宠物应返回 404（或 400）。"""
    fake_id = pet_api.random_pet_id()
    with allure.step(f"GET /pet/{fake_id} 查询不存在的宠物"):
        resp = pet_api.get_pet(fake_id)
    with allure.step("断言返回 404"):
        assert resp.status_code in (404, 400), f"预期 404/400，实际 {resp.status_code}"


# ---------------------------------------------------------------- 创建
@allure.story("创建宠物")
@allure.severity(allure.severity_level.BLOCKER)
def test_create_pet(pet_api: PetApi):
    """正向：创建宠物成功后，返回体各字段应与请求一致。"""
    pet_id, resp = pet_api.create_pet(name="create_doggie", status="available")
    try:
        with allure.step("POST /pet 创建宠物"):
            assert resp.status_code == 200, f"创建宠物失败: {resp.status_code} {resp.text[:200]}"
        with allure.step("断言返回体字段与结构约束"):
            body = resp.json()
            _assert_pet_body(body, pet_id, "create_doggie", "available")
    finally:
        _delete_quietly(pet_api, pet_id)


# ---------------------------------------------------------------- 更新
@allure.story("更新宠物")
@allure.severity(allure.severity_level.NORMAL)
def test_update_pet(pet_api: PetApi):
    """正向：PUT 整体更新后，再次查询应看到新的名称与状态。"""
    pet_id, _ = pet_api.create_pet(name="before_update", status="available")
    try:
        with allure.step("PUT /pet 整体更新宠物"):
            payload = pet_api.build_payload(pet_id, name="after_update", status="sold")
            resp = pet_api.update_pet(payload)
            assert resp.status_code == 200, f"更新宠物失败: {resp.status_code} {resp.text[:200]}"
        with allure.step("再次查询验证更新结果"):
            get_resp = pet_api.get_pet(pet_id)
            assert get_resp.status_code == 200
            body = get_resp.json()
            _assert_pet_body(body, pet_id, "after_update", "sold")
            assert body["name"] == "after_update", "更新后名称未生效"
            assert body["status"] == "sold", "更新后状态未生效"
    finally:
        _delete_quietly(pet_api, pet_id)


# ---------------------------------------------------------------- 删除
@allure.story("删除宠物")
@allure.severity(allure.severity_level.NORMAL)
def test_delete_pet(pet_api: PetApi):
    """正向：删除成功后，再查询同一 ID 应返回 404。"""
    pet_id, resp = pet_api.create_pet(name="to_delete")
    assert resp.status_code == 200, "前置创建宠物失败"
    with allure.step("DELETE /pet/{id} 删除宠物"):
        del_resp = pet_api.delete_pet(pet_id)
        assert del_resp.status_code == 200, f"删除宠物失败: {del_resp.status_code} {del_resp.text[:200]}"
    with allure.step("删除后再次查询应 404"):
        get_resp = pet_api.get_pet(pet_id)
        assert get_resp.status_code == 404, f"删除后仍可查询到宠物: {get_resp.status_code}"


@allure.story("删除异常场景")
@pytest.mark.negative
def test_delete_non_exist_pet(pet_api: PetApi):
    """反向：删除不存在的宠物应返回 404（幂等性校验）。"""
    fake_id = pet_api.random_pet_id()
    with allure.step(f"DELETE /pet/{fake_id} 删除不存在的宠物"):
        resp = pet_api.delete_pet(fake_id)
    with allure.step("断言返回 404"):
        assert resp.status_code in (404, 400), f"预期 404/400，实际 {resp.status_code}"


# ---------------------------------------------------------------- 按状态查询（参数化）
@allure.story("按状态查询")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("status", ["available", "pending", "sold"],
                         ids=["available", "pending", "sold"])
def test_find_pets_by_status(pet_api: PetApi, status: str):
    """参数化：按不同状态过滤宠物列表，返回项状态应与查询参数一致。"""
    with allure.step(f"GET /pet/findByStatus?status={status}"):
        resp = pet_api.find_by_status(status)
        assert resp.status_code == 200, f"按状态查询失败: {resp.status_code} {resp.text[:200]}"
    with allure.step("断言列表中的宠物状态与查询一致"):
        pets = resp.json()
        assert isinstance(pets, list), "返回体应为宠物列表"
        mismatched = [p for p in pets if p.get("status") != status]
        assert not mismatched, f"存在 {len(mismatched)} 只状态不匹配的宠物"
