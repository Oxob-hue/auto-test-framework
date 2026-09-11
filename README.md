# 全栈自动化测试实战项目（接口 + Web）

> 面向测试岗位求职展示的自动化测试实战项目，包含两大被测对象：
> - **Petstore 接口自动化**（RESTful API，Requests + Pytest + JSON 数据驱动 + jsonschema 结构校验）
> - **SauceDemo Web 自动化**（Selenium + Page Object，含下单全流程 E2E）
>
> 集成 **Allure** 可视化报告，失败自动收集「日志 + 截图 + 页面源码」；
> 内置**失败自动重试**（仅基础设施类异常）与 **GitHub Actions CI/CD 流水线**。
> 当前全量用例 **47 个，全部通过**（接口 20 + Web 27）。

---

## ✨ 项目亮点

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
│   ├── inventory_page.py        # 商品列表页（排序 / 详情跳转 / 列表移除 / 菜单退出）
│   ├── product_detail_page.py   # 商品详情页
│   ├── cart_page.py             # 购物车页（数量/名称/角标/继续购物/移除）
│   ├── checkout_page.py         # 结算页（信息/金额/取消/完成）
│   └── checkout_page.py         # 结算页（信息/总览/完成/表单校验）
├── tests/                       # 测试用例层（唯一的 conftest 全局夹具）
│   ├── conftest.py              # driver(edge/chrome)/api/pet_api + 失败自动收集
│   ├── test_pet.py              # 接口：增删改查 + schema 校验 + 异常 + 状态参数化
│   ├── test_pet_contract.py     # 接口：健壮性与契约（边界/幂等/非法入参/响应契约）
│   ├── test_pet_param.py        # 接口：JSON 数据驱动创建
│   ├── test_login.py            # Web：登录正向/反向 + 购物车主流程
│   ├── test_auth_guard.py       # Web：访问控制（未登录重定向）+ 退出登录
│   ├── test_inventory.py        # Web：排序 4 种 / 详情一致性 / 多商品加购 / 列表移除
│   ├── test_cart.py             # Web：购物车空态 / 继续购物 / 部分移除 / 角标消失
│   └── test_checkout.py         # Web：下单 E2E + 金额计算 + 取消下单 + 表单校验
├── test_data/
│   ├── pet_data.json            # 参数化测试数据
│   └── pet_response_schema.json # 接口响应结构约束（jsonschema）
├── scripts/
│   └── defect_probe.py          # 被测系统缺陷探测（真实取证，不参与回归）
├── docs/                        # 测试与求职文档
│   ├── 测试计划.md               # 测试计划（项目版：范围/策略/环境/风险/排期）
│   ├── 测试用例表.md             # 全量 47 条用例明细（编号/步骤/预期/实现位置/marker）
│   ├── 测试设计说明.md           # 设计思路（等价类/正反向/数据/稳定性）
│   ├── 测试报告.md               # 测试报告（真实执行结果与结论）
│   ├── 测试报告模板.md           # 报告模板（可复用于其他项目）
│   ├── 缺陷记录表.md             # 缺陷记录（框架 4 条 + 被测系统 2 条）
│   ├── 缺陷与踩坑记录.md         # 踩坑复盘（含跨浏览器稳定性完整排障过程）
│   ├── 缺陷复现演示.md           # 被测系统缺陷（problem_user 取证）
│   ├── 简历项目描述.md           # 简历可粘贴文案 + 技能清单 + 红线提醒
│   ├── 简历模板.html             # 可填写/可打印（导出 PDF）的简历模板
│   ├── 面试自我介绍与项目讲解话术.md  # 30 秒自我介绍 + 2 分钟讲解 + 追问速答
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

**当前状态：CI 已跑通（徽章 passing）**，47 条用例在 ubuntu + Chrome 无头环境全部通过，
Allure 报告已自动发布到 GitHub Pages。

- 在线 Allure 报告：**https://Oxob-hue.github.io/auto-test-framework/**
- 最近一次全绿运行：https://github.com/Oxob-hue/auto-test-framework/actions/runs/34560240548

首次推送与排错指引见 [`docs/GitHub推送与CI首次运行指南.md`](docs/GitHub推送与CI首次运行指南.md)（含 PAT 生成与常见问题）。

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
collected 47 items
tests\test_auth_guard.py ...     tests\test_pet.py .........
tests\test_cart.py ....          tests\test_pet_contract.py ........
tests\test_checkout.py ......    tests\test_pet_param.py ...
tests\test_inventory.py .......  tests\test_login.py .......

=================== 47 passed, 1 rerun in 62.14s (0:01:02) ===================
```

Allure 摘要：passed=47, failed=0, broken=0, skipped=0。
GitHub Actions 流水线产物：`allure-report` Artifact + GitHub Pages 在线报告。

### ⚡ 执行效率（并发优化）

| 执行方式 | 耗时 | 说明 |
|----------|------|------|
| 并行执行 `pytest tests -n 4` | 62.14s | pytest-xdist，4 worker 并发（47 条全量，含 1 次基础设施类重试） |
| 无头全量（近似 CI） | 191.12s | 单进程 + Edge 无头，47 条全部通过（运行条件与 CI 最接近） |
| Web 子集顺序执行 | 176.29s | 27 条 Web 用例单进程逐条执行 |

> 接口用例以网络等待为主、Web 用例浏览器会话相互独立，天然适合并行；
> 全量统计与提速数据见 [`docs/测试报告模板.md`](docs/测试报告模板.md)。

---

## 📚 测试流程与求职文档

**测试流程文档（覆盖"计划 → 用例 → 执行 → 缺陷 → 报告"完整闭环）**
- [`docs/测试计划.md`](docs/测试计划.md)：项目版测试计划（范围 47 条、策略、环境、准入准出、风险应对、阶段安排）；
- [`docs/测试用例表.md`](docs/测试用例表.md)：全量 47 条用例明细（编号 / 类型 / 优先级 / 前置 / 步骤 / 预期 / 代码位置 / marker）；
- [`docs/测试设计说明.md`](docs/测试设计说明.md)：等价类与边界、正反向分离、数据策略、稳定性与可观测性设计；
- [`docs/测试报告.md`](docs/测试报告.md)：真实执行报告（47/47 通过、分模块结果、缺陷统计、风险遗留、结论建议）；
- [`docs/缺陷记录表.md`](docs/缺陷记录表.md)：缺陷记录（框架自身 4 条已修复 + 被测系统 2 条已取证）；
- [`docs/测试报告模板.md`](docs/测试报告模板.md)：可复用的报告模板。

**问题定位与复盘**
- [`docs/缺陷与踩坑记录.md`](docs/缺陷与踩坑记录.md)：跨浏览器稳定性完整排障过程 + PO 缩进 / 日志流 / 重复 conftest 复盘 + 面试追问速答；
- [`docs/缺陷复现演示.md`](docs/缺陷复现演示.md)：被测系统（SauceDemo problem_user）真实取证的 2 个缺陷。

**求职材料**
- [`docs/简历项目描述.md`](docs/简历项目描述.md)：可粘贴的简历项目经历 + 技能清单 + 红线提醒；
- [`docs/简历模板.html`](docs/简历模板.html)：可填写、可打印导出 PDF 的简历模板；
- [`docs/面试自我介绍与项目讲解话术.md`](docs/面试自我介绍与项目讲解话术.md)：30 秒自我介绍 + 2 分钟项目讲解 + 追问速答；
- [`docs/GitHub推送与CI首次运行指南.md`](docs/GitHub推送与CI首次运行指南.md)：PAT 推送 + 首次 CI 跑绿步骤。

**文档导出（Excel / PDF，便于发给面试官或打印）**
```bash
python scripts/export_docs.py   # Markdown → docs/export/测试用例表.xlsx、.csv 与 html/
python scripts/print_pdf.py     # html/ → docs/export/测试计划.pdf、测试用例表.pdf、测试报告.pdf
```

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
