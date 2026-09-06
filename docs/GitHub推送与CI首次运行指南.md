# GitHub 推送与首次 CI 运行指南

> 目标：把本项目推到 GitHub，触发 `.github/workflows/ci.yml`，完成**首次真实跑绿**。
> 本机当前未安装 Git、无本地仓库；GitHub 已不再支持账号密码推送，必须使用 **Personal Access Token (PAT)**。

---

## ⚠️ 安全须知（先读）

1. **不要把账号密码/Token 粘贴到聊天、Issue、代码里**；一旦出现在任何对话或日志中即视为泄露；
2. PAT 权限最小化：仅勾选 `repo`（若想后续自动部署 Pages 再按需加 `workflow`）；
3. 若此前曾在别处暴露过密码，请立即去 GitHub → Settings → Security 修改/开启 2FA；
4. 本机 `.gitignore` 已排除 venv、allure、logs、.idea 等产物，不会把环境/凭据推上去。

## 1. 生成 PAT（个人访问令牌）

1. 登录 GitHub → 右上角头像 → **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)**；
2. 勾选 **repo**（本指南只需要此权限），过期时间建议 90 天；
3. 生成后**立即复制保存**（只显示一次），形如 `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`。

## 2. 安装 Git（本机当前未安装）

任选其一：
- 命令：`winget install --id Git.Git -e --source winget`（Windows 应用商店源，重启终端生效）；
- 或官网下载安装：https://git-scm.com/download/win（一路 Next 即可）。

安装完成后验证：`git --version`。

## 3. 初始化本地仓库并提交

在项目根目录执行：

```bash
git init -b main
git add .
git status          # 确认没有 venv/、allure-*、logs/ 等产物被加入
git commit -m "feat: 全栈自动化测试项目（接口+Web，Pytest/Allure/PO，含 CI 流水线）"
```

若 `git status` 出现不应入库的文件，先补 `.gitignore` 规则再提交。

## 4. 创建远程仓库

网页方式：GitHub → New repository → 命名（如 `auto-test-framework`）→ **不要**勾选 README/.gitignore（避免冲突）→ Create。

## 5. 推送并触发 CI

```bash
git remote add origin https://github.com/<你的用户名>/auto-test-framework.git
git push -u origin main
```

> HTTPS 推送时提示输入用户名/密码：用户名填 GitHub 用户名，**密码处粘贴 PAT**（不是账号密码）。

## 6. 查看首次运行

1. 打开仓库页 → **Actions** 标签，可看到 `自动化回归 CI` 流水线；
2. 期望看到三个 Job：`接口自动化`、`Web 自动化`、`生成 Allure 报告` 全部绿；
3. 点进 `Web 自动化` Job：环境变量已把浏览器切为 **Chrome 无头**，
   首次运行 Selenium Manager 会自动联网下载匹配的 chromedriver（约 1–3 分钟，属正常）。

### 首次运行常见排错
| 现象 | 处理 |
|------|------|
| Web Job 下载 chromedriver 失败 | 重跑（Actions → Re-run）；或确认 ubuntu-latest 自带 Chrome 可用 |
| 接口用例偶发失败（公网环境抖动） | 项目已配重试（仅基础设施类异常），可 Re-run jobs |
| 想跳过 Web 只跑接口 | 在 Workflow 中临时注释 `web-tests` 的 `needs` 引用 |
| cron 不执行 | 确认分支名是 main/master，且仓库默认分支与 triggers 一致 |

## 7. 收尾：给 README 换真实徽章

流水线第一次跑绿后，README「CI/CD」一节中的徽章占位可替换为真实地址：

```markdown
[![CI](https://github.com/<你的用户名>/auto-test-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/<你的用户名>/auto-test-framework/actions/workflows/ci.yml)
```

## 8. （可选）把报告发布到 GitHub Pages

在仓库 Settings → Pages → Build and deployment → GitHub Actions 启用后，
可在 workflow 中追加 `actions/deploy-pages` 步骤把 `allure-report` 发布为在线报告。
