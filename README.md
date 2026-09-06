# 全栈自动化测试实战项目（接口 + Web）

> 面向测试岗位求职展示的自动化测试实战项目，包含两大被测对象：
> - **Petstore 接口自动化**（RESTful API，Requests + Pytest + JSON 数据驱动 + jsonschema 结构校验）
> - **SauceDemo Web 自动化**（Selenium + Page Object，含下单全流程 E2E）
>
> 集成 **Allure** 可视化报告，失败自动收集「日志 + 截图 + 页面源码」；
> 内置**失败自动重试**（仅基础设施类异常）与 **GitHub Actions CI/CD 流水线**。
> 当前全量用例 **23 个，全部通过**（接口 12 + Web 11）。

---

## ✨ 项目亮点（面试自我介绍可直接引用）

1. **清晰的分层架构**：测试用例 → 页面/接口对象层 → 公共封装层 → 配置层，低耦合、易维护；
2. **接口自动化工程化**：Session 复用 + 统一超时 + 请求/响应日志；**jsonschema 响应结构校验**；
   测试数据前后置自动准备与清理，用例可重复运行、不残留脏数据；
3. **Web 自动化 PO 模式**：BasePage 统一封装显式等待与元素操作，业务页面对象隔离定位器，
   覆盖登录 → 加购 → 结算 → 下单成功与表单校验异常等完整业务规则；
4. **配置与运行目录解耦**：所有路径基于项目根目录（pathlib）；配置集中在 `config.ini`
   （环境地址/浏览器/驱动/等待超时/无头模式），并支持**环境变量覆盖**（`TEST_WEB_HEADLESS=true` 等），
   同一套用例可同时跑在本地与无界面 CI；
5. **CI/CD 就绪**：内置 GitHub Actions 流水线 —— push / 定时触发全量回归，
   接口在 ubuntu 运行、Web 用 Chrome 无头运行，自动汇总生成 Allure 报告（见下方「CI/CD」）；
6. **稳定性设计**：失败自动重试**仅针对基础设施类异常**（浏览器/驱动/网络抖动），
   断言类失败不重试，避免用重试掩盖真实缺陷；
7. **用例设计规范**：正向 / 反向分离，参数化 + JSON 数据驱动，marker 划分
   （api / web / smoke / negative），Allure 标注（epic / feature / story / severity / step）；
8. **失败自愈可观测**：失败自动附加运行日志尾部、页面截图与 DOM 源码，问题快速定位；
9. **求职素材完整**：提供 `docs/测试设计说明.md`（设计思路）与 `docs/缺陷与踩坑记录.md`
   （缺陷模板 + 3 个真实踩坑复盘），面试可直接翻给面试官看。

---

## 🛠 技术栈

| 分类 | 技术 / 工具 |
|------|-------------|
| 语言 | Python 3.10+（3.14 验证通过） |
| 测试框架 | Pytest 9.x |
| 接口测试 | Requests（Session 复用）+ jsonschema |
| Web 测试 | Selenium 4.x + Edge/Chrome（Selenium Manager） |
| 报告 | Allure + allure-pytest |
| 稳定性 | pytest-rerunfailures（仅基础设施类失败重试） |
| 性能 | pytest-xdist 并行（实测 -n 4 提速约 2.4 倍） |
| CI/CD | GitHub Actions（push/定时/手动触发 + 报告产物） |
| 数据驱动 | JSON + pytest.mark.parametrize |
| 设计模式 | Page Object / 业务对象封装 |
| 版本控制 | Git / GitHub |

---

## 📁 项目结构

```
.
├── .github/workflows/           # CI/CD 流水线
│   └── ci.yml                   # push/定时/手动触发 → 接口+Web回归 → Allure 报告
├── api/                         # 接口业务对象层（对应 Web 端 Page Object）
│   └── pet_api.py               # Petstore 宠物 CRUD 与报文构造
├── common/                      # 公共能力层
│   ├── config_util.py           # config.ini + 环境变量覆盖 + 项目根目录定位
│   ├── json_schema_util.py      # jsonschema 响应结构校验工具
│   ├── logger.py                # 日志（控制台 + 文件，自动建目录）
│   └── request_util.py          # HTTP 请求封装（Session/超时/日志/URL 拼接）
├── pages/                       # Web 页面对象层
│   ├── base_page.py             # 页面基类：显式等待与通用操作
│   ├── login_page.py            # 登录页
│   ├── inventory_page.py        # 商品列表页（含排序、多商品加购）
│   ├── cart_page.py             # 购物车页
│   └── checkout_page.py         # 结算页（信息/总览/完成/表单校验）
├── tests/                       # 测试用例层（唯一的 conftest 全局夹具）
│   ├── conftest.py              # driver(edge/chrome)/api/pet_api + 失败自动收集
│   ├── test_pet.py              # 接口：增删改查 + schema 校验 + 异常 + 状态参数化
│   ├── test_pet_param.py        # 接口：JSON 数据驱动创建
│   ├── test_login.py            # Web：登录正向/反向 + 购物车主流程
│   ├── test_inventory.py        # Web：商品排序 / 多商品加购
│   └── test_checkout.py         # Web：下单全流程 E2E + 表单校验异常
├── test_data/
│   ├── pet_data.json            # 参数化测试数据
│   └── pet_response_schema.json # 接口响应结构约束（jsonschema）
├── scripts/
│   └── defect_probe.py          # 被测系统缺陷探测（真实取证，不参与回归）
├── docs/                        # 求职展示文档
│   ├── 测试设计说明.md           # 设计思路（等价类/正反向/数据/稳定性）
│   ├── 缺陷与踩坑记录.md         # 框架自身踩坑复盘 + 缺陷模板
│   ├── 缺陷复现演示.md           # 被测系统缺陷（problem_user 取证）
│   ├── 测试计划.md               # 测试计划模板（范围/策略/风险/排期）
│   ├── 测试报告模板.md           # 报告模板（含真实统计与提速数据）
│   └── GitHub推送与CI首次运行指南.md  # PAT 推送 + 首次跑绿步骤
├── config.ini                   # 环境配置（唯一配置入口）
├── pytest.ini                   # Pytest 配置（markers/addopts/重试策略）
├── requirements.txt             # 依赖清单（锁定版本）
├── .gitignore
└── README.md
```

> 运行生成的 `allure-results/`、`allure-report/`、`logs/` 等产物均已在 `.gitignore` 中排除。

---

## 🚀 快速开始

### 1. 环境准备

```bash
# ① 创建并激活虚拟环境（Python 3.10+）
python -m venv venv
venv\Scripts\activate        # Windows

# ② 安装依赖
pip install -r requirements.txt

# ③ 准备浏览器驱动与 Allure 命令行工具
#    Edge：下载与浏览器版本匹配的 msedgedriver 并写入 config.ini；
#    Chrome：无需手动装驱动，Selenium Manager 会自动匹配（适合 CI）。
```

### 2. 修改配置（可选）

编辑 `config.ini` 按本机环境调整；也可用环境变量覆盖（优先级更高），例如：

```bash
# 无头模式 + Chrome（等价于 CI 的运行方式，无需改任何文件）
TEST_WEB_HEADLESS=true TEST_WEB_BROWSER=chrome python -m pytest -m web
```

### 3. 运行用例

```bash
# 仅接口用例
python -m pytest -m api

# 仅 Web 用例（需本机可启动浏览器）
python -m pytest -m web

# 冒烟（核心主流程）
python -m pytest -m smoke

# 全量回归（addopts 已默认输出 Allure 结果到 allure-results）
python -m pytest tests
```

失败重试策略默认开启（仅对基础设施类异常重试 1 次），如需关闭：`python -m pytest --reruns 0`。

### 4. 生成并查看 Allure 报告

```bash
allure generate allure-results -o allure-report --clean
allure open allure-report
```

---

## 🤖 CI/CD（GitHub Actions）

`.github/workflows/ci.yml` 提供开箱即用的流水线：

| 触发方式 | 内容 |
|----------|------|
| push（main/master） | 全量回归 |
| pull_request | 全量回归（质量门禁） |
| schedule（每天 01:00 UTC） | 定时回归 |
| workflow_dispatch | 手动触发 |

流水线分三个 Job：

1. `api-tests`：ubuntu 上运行 `-m api`；
2. `web-tests`：ubuntu 上通过环境变量切到 **Chrome 无头**运行 `-m web`（Selenium Manager 自动匹配驱动）；
3. `allure-report`：汇总两个 Job 的 Allure 结果 → 生成报告 → 上传 Artifact（即使有失败也会生成，便于查看失败详情）。

使用方式：把项目推送到 GitHub 即自动生效（Web Job 会在首次运行时联网下载匹配的 chromedriver）。
首次推送与跑绿的逐步指引见 [`docs/GitHub推送与CI首次运行指南.md`](docs/GitHub推送与CI首次运行指南.md)
（含 PAT 生成、排错与徽章替换）。流水线跑绿后可将下方占位替换为真实徽章：

[![CI](https://github.com/Oxob-hue/auto-test-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/Oxob-hue/auto-test-framework/actions/workflows/ci.yml)

---

## 🧪 接口自动化说明（Petstore）

- 被测接口：`https://petstore.swagger.io/v2`（公开练习环境）
- 分层调用链：`tests` → `PetApi`（业务封装）→ `RequestUtil`（HTTP）→ `config.ini`
- `RequestUtil` 设计：Session 复用（连接池）、统一超时防挂死、支持相对/绝对 URL、自动输出请求与响应日志
- 断言策略：**状态码 + 业务字段 + jsonschema 结构约束**三层校验
  （约束字段类型 / 必填项 / status 枚举，防止前后端契约悄悄漂移）
- 测试数据管理：
  - `created_pet_id` fixture：模块前置自动创建宠物，模块结束后自动删除；
  - 各用例在 `finally` 中幂等清理自身数据，保证重复执行不残留、不冲突；
  - 宠物 ID 支持按时间随机生成，避免用例间数据串扰。
- 覆盖场景（12 条）：
  - 正向：创建 / 查询 / PUT 更新 / 删除后再查 404；
  - 反向：查询不存在宠物 404、删除不存在宠物 404；
  - 数据驱动：JSON 多组数据创建，覆盖 available / pending / sold 三种状态；
  - 参数化查询：`findByStatus` 过滤结果状态一致性校验。

## 🌐 Web 自动化说明（SauceDemo）

- 被测站点：`https://www.saucedemo.com/`（公开练习站点）
- 设计模式：Page Object —— `BasePage` 封装显式等待（可见/可点击）、输入、取值等方法，业务页面只维护定位器与操作步骤；
- 覆盖场景（11 条）：
  - 登录正向：standard_user / problem_user 成功进入商品页；
  - 登录反向：锁定账号 / 密码错误 / 空用户名 / 空密码的错误提示校验；
  - 购物车：登录 → 加购（角标校验）→ 购物车数量校验 → 移除商品；
  - 商品排序：按价格升序后断言**页面实际展示**的价格列表升序；
  - 多商品加购：两件商品 → 角标 2 → 购物车条目 2；
  - 下单全流程 E2E：登录 → 加购 → 购物车 → 填写收货信息 → 订单总览 → Finish → 成功提示断言；
  - 表单校验异常：缺邮编被拦截并提示，且不进入订单总览页。

## 📊 失败自动收集与稳定性（Allure + 重试）

用例执行失败时，通过唯一 conftest 中的 `pytest_runtest_makereport` 钩子自动附加：

1. 运行日志尾部（`logs/test.log` 最近 300 行）；
2. Web 页面截图（PNG）；
3. 页面 DOM 源码。

失败重试策略见 `pytest.ini`：`--only-rerun "(WebDriverException|TimeoutException|ConnectionError|...)"`，
即浏览器/驱动/网络类抖动自动重试，真实断言失败不被掩盖。

---

## ✅ 当前回归结果（本地全量）

```
collected 23 items
tests\test_checkout.py  ..      tests\test_pet.py .........
tests\test_inventory.py ..      tests\test_pet_param.py ...
tests\test_login.py .......

========================= 23 passed in 63.93s (0:01:03) =========================
```

Allure 摘要：passed=23, failed=0, broken=0, skipped=0。
GitHub Actions 流水线产物：`allure-report` Artifact（可下载或部署到 GitHub Pages）。

### ⚡ 执行效率（并发优化）

| 执行方式 | 耗时 | 说明 |
|----------|------|------|
| 顺序执行（默认） | 63.93s | 单进程逐条执行 |
| 并行执行 `pytest tests -n 4` | 26.65s | pytest-xdist，4 worker 并发，**约 2.4 倍提速** |

> 接口用例以网络等待为主、Web 用例浏览器会话相互独立，天然适合并行；
> 全量统计与提速数据见 [`docs/测试报告模板.md`](docs/测试报告模板.md)。

---

## 📚 求职展示文档

- [`docs/测试设计说明.md`](docs/测试设计说明.md)：分层思路、等价类/正反向/边界设计、数据策略、稳定性设计、用例清单；
- [`docs/缺陷与踩坑记录.md`](docs/缺陷与踩坑记录.md)：缺陷记录模板 + 3 个真实踩坑复盘（PO 缩进 bug、logger 写入已关闭流、重复 conftest）+ 面试追问速答；
- [`docs/缺陷复现演示.md`](docs/缺陷复现演示.md)：被测系统（SauceDemo problem_user）**真实取证**的 2 个缺陷（图片错乱、排序失效），回答"你测出过什么问题"；
- [`docs/测试计划.md`](docs/测试计划.md)：测试计划模板（范围/策略/风险/排期）；
- [`docs/测试报告模板.md`](docs/测试报告模板.md)：测试报告模板（含真实统计与提速数据）；
- [`docs/GitHub推送与CI首次运行指南.md`](docs/GitHub推送与CI首次运行指南.md)：PAT 推送 + 首次 CI 跑绿步骤。

## 📝 项目产出与学习路线

- 接口自动化测试脚本（Pytest + Requests + 数据驱动 + schema 校验）
- Web 自动化测试脚本（Pytest + Selenium + PO + E2E）
- Allure 可视化报告 + GitHub Actions 流水线 + pytest-xdist 并行提速
- 测试设计 / 测试计划 / 测试报告 / 缺陷记录 / 缺陷取证文档

可继续扩展的方向：GitHub Pages 自动发布报告、多环境配置（dev/staging）、
私有 mock 环境替代公网依赖、接口契约测试、AI 辅助生成测试数据等。

---

## 🤝 声明

本项目仅用于学习与求职展示，被测对象均为公开练习平台，不涉及真实业务数据。
代码结构参考企业级测试框架设计，适合测试开发 / 自动化测试岗位的求职项目沉淀。

---

**作者**：侯静然
**更新**：2026 年 9 月
