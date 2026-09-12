"""接口业务链路用例：状态流转与数据一致性（Petstore）。

与单接口 CRUD 用例的区别：这里验证**跨接口的业务链路**——
创建后能否在状态列表中查到、状态变更后在新旧列表中"此消彼长"、
更新与删除能否在查询与列表两个视图上保持一致。

公共练习环境为**最终一致**（列表接口可能存在秒级延迟），因此统一采用
"带超时的轮询等待"而不是固定 sleep，兼顾稳定性与执行速度。
"""
import time
from typing import Callable

import allure
import pytest

from api.pet_api import PetApi

pytestmark = [
    pytest.mark.api,
    allure.epic("接口自动化"),
    allure.feature("业务链路与数据一致性"),
]

POLL_TIMEOUT = 20.0
POLL_INTERVAL = 1.0


def _wait_until(predicate: Callable[[], bool], message: str,
                timeout: float = POLL_TIMEOUT) -> None:
    """轮询直到条件成立（用于最终一致性校验），超时抛断言失败。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if predicate():
                return
        except Exception:  # noqa: BLE001 网络抖动按"未达成"处理，继续轮询
            pass
        time.sleep(POLL_INTERVAL)
    raise AssertionError(f"{message}（等待 {timeout:.0f}s 仍未满足）")


def _delete_quietly(pet_api: PetApi, pet_id: int) -> None:
    pet_api.delete_pet(pet_id)


def _find_in_status(pet_api: PetApi, pet_id: int, status: str):
    """在指定状态列表中查找宠物，找到返回宠物对象，否则返回 None。"""
    resp = pet_api.find_by_status(status)
    if resp.status_code != 200:
        return None
    for pet in resp.json():
        if pet.get("id") == pet_id:
            return pet
    return None


@allure.story("创建后可在状态列表查到")
@allure.severity(allure.severity_level.CRITICAL)
def test_created_pet_appears_in_status_list(pet_api: PetApi):
    """业务链路：创建宠物 → 该宠物应出现在对应状态的查询列表中（最终一致）。"""
    pet_id, resp = pet_api.create_pet(name="biz_created_pet", status="available")
    try:
        with allure.step("创建宠物"):
            assert resp.status_code == 200, f"创建失败: {resp.status_code} {resp.text[:200]}"
        with allure.step("轮询确认出现在 available 列表"):
            _wait_until(lambda: _find_in_status(pet_api, pet_id, "available") is not None,
                        f"创建的宠物 {pet_id} 未出现在 available 列表中")
    finally:
        _delete_quietly(pet_api, pet_id)


@allure.story("状态流转一致性")
@allure.severity(allure.severity_level.CRITICAL)
def test_status_transition_moves_between_lists(pet_api: PetApi):
    """业务链路：状态 available → sold 后，应在新列表可见、在旧列表不可见。"""
    pet_id, resp = pet_api.create_pet(name="biz_status_flow", status="available")
    try:
        assert resp.status_code == 200, "前置创建失败"
        with allure.step("初始状态：应出现在 available 列表"):
            _wait_until(lambda: _find_in_status(pet_api, pet_id, "available") is not None,
                        "初始宠物未出现在 available 列表")

        with allure.step("更新状态为 sold"):
            update = pet_api.update_pet(pet_api.build_payload(pet_id, name="biz_status_flow", status="sold"))
            assert update.status_code == 200, f"更新失败: {update.status_code}"

        with allure.step("轮询确认已进入 sold 列表"):
            _wait_until(lambda: _find_in_status(pet_api, pet_id, "sold") is not None,
                        "状态更新后未出现在 sold 列表")
        with allure.step("轮询确认已从 available 列表消失"):
            _wait_until(lambda: _find_in_status(pet_api, pet_id, "available") is None,
                        "状态更新后仍残留在 available 列表")
    finally:
        _delete_quietly(pet_api, pet_id)


@allure.story("更新在查询与列表两端一致")
@allure.severity(allure.severity_level.NORMAL)
def test_update_reflected_in_query_and_list(pet_api: PetApi):
    """业务链路：PUT 更新名称后，单查接口与状态列表两个视图都应反映新值。"""
    pet_id, resp = pet_api.create_pet(name="biz_before_update", status="pending")
    try:
        assert resp.status_code == 200, "前置创建失败"
        with allure.step("更新名称为 biz_after_update"):
            payload = pet_api.build_payload(pet_id, name="biz_after_update", status="pending")
            assert pet_api.update_pet(payload).status_code == 200

        with allure.step("单查接口返回新名称"):
            assert pet_api.get_pet(pet_id).json()["name"] == "biz_after_update"

        with allure.step("列表接口也返回新名称（最终一致）"):
            _wait_until(
                lambda: (_find_in_status(pet_api, pet_id, "pending") or {}).get("name") == "biz_after_update",
                "状态列表未同步更新后的名称",
            )
    finally:
        _delete_quietly(pet_api, pet_id)


@allure.story("删除后从列表消失")
@allure.severity(allure.severity_level.NORMAL)
def test_delete_removes_pet_from_list(pet_api: PetApi):
    """业务链路：删除后，该宠物应从状态列表中消失（数据不留残影）。"""
    pet_id, resp = pet_api.create_pet(name="biz_to_delete", status="available")
    assert resp.status_code == 200, "前置创建失败"
    with allure.step("确认创建后已在列表中"):
        _wait_until(lambda: _find_in_status(pet_api, pet_id, "available") is not None,
                    "创建后未出现在列表中")

    with allure.step("删除宠物"):
        assert pet_api.delete_pet(pet_id).status_code == 200

    with allure.step("轮询确认已从列表消失"):
        _wait_until(lambda: _find_in_status(pet_api, pet_id, "available") is None,
                    "删除后仍出现在列表中")
