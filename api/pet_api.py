"""Petstore 宠物业务接口对象。

作用类似 Web 自动化中的 Page Object：把“创建宠物、查询宠物、删除宠物”等业务操作
封装成可读性强的对象方法，测试用例不再直接拼 URL 与报文，降低耦合、便于维护。
"""
import time
from typing import Any, Optional

import requests

from common.request_util import RequestUtil


class PetApi:
    """封装 Petstore /pet 相关接口调用与宠物数据构造。"""

    BASE_PATH = "/pet"

    def __init__(self, client: Optional[RequestUtil] = None):
        self.client = client or RequestUtil()

    @staticmethod
    def random_pet_id() -> int:
        """生成基于当前时间的随机宠物 ID，保证用例重复执行不冲突。"""
        return int(time.time_ns() % 9_000_000_000) + 1_000_000_000

    @staticmethod
    def build_payload(pet_id: int, name: str = "doggie", status: str = "available") -> dict:
        """构造符合 Petstore 规范的宠物报文。"""
        return {
            "id": pet_id,
            "category": {"id": 1, "name": "dog"},
            "name": name,
            "photoUrls": ["https://example.com/dog.png"],
            "tags": [{"id": 1, "name": "auto_test"}],
            "status": status,
        }

    # ---------------- 业务操作 ----------------
    def create_pet(self, pet_id: Optional[int] = None, name: str = "doggie",
                   status: str = "available") -> tuple:
        """创建宠物，返回 (pet_id, response)。pet_id 缺省时自动生成。"""
        pet_id = pet_id if pet_id is not None else self.random_pet_id()
        resp = self.client.post(self.BASE_PATH, json=self.build_payload(pet_id, name, status))
        return pet_id, resp

    def get_pet(self, pet_id: int) -> requests.Response:
        """按 ID 查询宠物。"""
        return self.client.get(f"{self.BASE_PATH}/{pet_id}")

    def update_pet(self, payload: dict) -> requests.Response:
        """整体更新宠物（PUT /pet）。"""
        return self.client.put(self.BASE_PATH, json=payload)

    def delete_pet(self, pet_id: int) -> requests.Response:
        """按 ID 删除宠物（幂等：不存在时返回 404）。"""
        return self.client.delete(f"{self.BASE_PATH}/{pet_id}")

    def find_by_status(self, status: str) -> requests.Response:
        """按状态查询宠物列表（available / pending / sold）。"""
        return self.client.get(f"{self.BASE_PATH}/findByStatus", params={"status": status})
