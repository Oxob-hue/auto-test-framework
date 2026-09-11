"""接口健壮性与契约用例（Petstore）。

设计思路：公开练习环境对"非法/边界入参"的校验并不严格，因此断言聚焦**契约底线**：
服务端不能 5xx、响应必须可解析、成功写入的数据必须可回读一致；对幂等/覆盖语义
（重复 ID、PUT 不存在的 ID）显式验证并锁定行为。
"""
import time

import allure
import pytest

from api.pet_api import PetApi
from common.json_schema_util import validate_response

pytestmark = [
    pytest.mark.api,
    allure.epic("接口自动化"),
    allure.feature("接口健壮性与契约"),
]

PET_SCHEMA = "test_data/pet_response_schema.json"


def _delete_quietly(pet_api: PetApi, pet_id: int) -> None:
    pet_api.delete_pet(pet_id)


@allure.story("边界数据")
@allure.severity(allure.severity_level.NORMAL)
def test_create_pet_with_chinese_and_symbol_name_roundtrip(pet_api: PetApi):
    """中文 + 表情符号名称应能正确写入并原样回读（编码正确性）。"""
    name = "测试宠物-🐶_v1"
    pet_id, resp = pet_api.create_pet(name=name)
    try:
        with allure.step("创建含中文与符号的宠物"):
            assert resp.status_code == 200, f"创建失败: {resp.status_code} {resp.text[:200]}"
            validate_response(resp.json(), PET_SCHEMA)
        with allure.step("回读名称应与写入完全一致"):
            get_resp = pet_api.get_pet(pet_id)
            assert get_resp.status_code == 200
            assert get_resp.json()["name"] == name, "中文/符号名称回读不一致"
    finally:
        _delete_quietly(pet_api, pet_id)


@allure.story("边界数据")
@allure.severity(allure.severity_level.NORMAL)
def test_create_pet_with_long_name(pet_api: PetApi):
    """超长名称（256 字符）应可写入并回读，且不出现 5xx。"""
    name = "L" * 256
    pet_id, resp = pet_api.create_pet(name=name)
    try:
        with allure.step("创建超长名称宠物"):
            assert resp.status_code == 200, f"创建失败: {resp.status_code}"
            assert resp.status_code < 500
        with allure.step("回读名称字段非空且长度合理"):
            get_resp = pet_api.get_pet(pet_id)
            assert get_resp.status_code == 200
            returned = get_resp.json()["name"]
            assert returned and len(returned) >= 200, f"超长名称疑似丢失: len={len(returned)}"
    finally:
        _delete_quietly(pet_api, pet_id)


@allure.story("幂等与覆盖语义")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_same_id_twice_second_wins(pet_api: PetApi):
    """同一 ID 重复创建应表现为覆盖：第二次写入的名称生效。"""
    pet_id = pet_api.random_pet_id()
    try:
        with allure.step("第一次创建 name=first_version"):
            _, resp1 = pet_api.create_pet(pet_id=pet_id, name="first_version")
            assert resp1.status_code == 200
        with allure.step("第二次以相同 ID 创建 name=second_version"):
            _, resp2 = pet_api.create_pet(pet_id=pet_id, name="second_version")
            assert resp2.status_code == 200
        with allure.step("回读应为第二次写入的值"):
            body = pet_api.get_pet(pet_id).json()
            assert body["name"] == "second_version", "重复创建未覆盖旧数据"
    finally:
        _delete_quietly(pet_api, pet_id)


@allure.story("幂等与覆盖语义")
@allure.severity(allure.severity_level.NORMAL)
def test_update_non_exist_pet_contract(pet_api: PetApi):
    """PUT 不存在的 ID：行为必须自洽（200=upsert 可查到 / 404=查不到）。"""
    pet_id = pet_api.random_pet_id()
    created = False
    try:
        with allure.step("PUT 一个不存在的宠物 ID"):
            resp = pet_api.update_pet(pet_api.build_payload(pet_id, name="upsert_probe"))
        with allure.step("校验行为自洽"):
            assert resp.status_code in (200, 404), f"非预期状态码: {resp.status_code}"
            get_resp = pet_api.get_pet(pet_id)
            if resp.status_code == 200:
                created = True
                assert get_resp.status_code == 200, "PUT 返回 200 但数据不可查询，契约不自洽"
                assert get_resp.json()["name"] == "upsert_probe"
            else:
                assert get_resp.status_code == 404, "PUT 返回 404 但数据却存在，契约不自洽"
    finally:
        if created:
            _delete_quietly(pet_api, pet_id)


@allure.story("异常入参")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.negative
def test_invalid_status_value_not_5xx(pet_api: PetApi):
    """非法 status 取值不应导致服务端 5xx（校验缺失属于可接受现状，但必须可解析）。"""
    pet_id, resp = pet_api.create_pet(name="invalid_status_pet", status="invalid_status")
    try:
        with allure.step("使用非法 status 创建宠物"):
            assert resp.status_code < 500, f"服务端 5xx: {resp.status_code} {resp.text[:200]}"
        with allure.step("响应可解析且可回读"):
            assert resp.json().get("id") == pet_id
            get_resp = pet_api.get_pet(pet_id)
            assert get_resp.status_code < 500
    finally:
        _delete_quietly(pet_api, pet_id)


@allure.story("异常入参")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.negative
def test_missing_required_fields_not_5xx(pet_api: PetApi):
    """缺少必填字段（name/photoUrls）时不应 5xx，且返回体可解析。"""
    pet_id = pet_api.random_pet_id()
    try:
        with allure.step("仅提交 id 字段创建宠物"):
            resp = pet_api.client.post(pet_api.BASE_PATH, json={"id": pet_id})
        with allure.step("断言未 5xx 且响应可解析"):
            assert resp.status_code < 500, f"服务端 5xx: {resp.status_code} {resp.text[:200]}"
            resp.json()  # 不可解析会直接抛异常
    finally:
        _delete_quietly(pet_api, pet_id)


@allure.story("响应契约")
@allure.severity(allure.severity_level.NORMAL)
def test_response_contract_content_type_and_latency(pet_api: PetApi, created_pet_id: int):
    """响应契约：Content-Type 为 JSON，且单次查询响应时间在合理范围（< 5s）。"""
    with allure.step("GET /pet/{id} 并记录耗时"):
        start = time.monotonic()
        resp = pet_api.get_pet(created_pet_id)
        elapsed = time.monotonic() - start
    with allure.step("断言状态码 / Content-Type / 响应时间"):
        assert resp.status_code == 200
        content_type = resp.headers.get("Content-Type", "")
        assert "application/json" in content_type, f"Content-Type 非 JSON: {content_type!r}"
        assert elapsed < 5.0, f"响应时间过长: {elapsed:.2f}s"


@allure.story("异常入参")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.negative
def test_find_by_status_invalid_value(pet_api: PetApi):
    """findByStatus 传入非法状态值：应返回空列表（200）或 400，不能 5xx。"""
    with allure.step("GET /pet/findByStatus?status=__invalid_status__"):
        resp = pet_api.find_by_status("__invalid_status__")
    with allure.step("断言 200（空列表）或 400"):
        assert resp.status_code in (200, 400), f"非预期状态码: {resp.status_code}"
        if resp.status_code == 200:
            assert isinstance(resp.json(), list), "返回体应为列表"
