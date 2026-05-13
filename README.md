# SJTU-ibot 🤖

上海交通大学智能通知助手 - 自动监控交大官网通知和 Canvas 课程更新

## ✨ 功能特性

- 🏫 **交大官网通知监控** - 自动抓取上海交通大学官网最新通知
- 📚 **Canvas 课程更新** - 监控 Canvas 平台课程公告和作业
- ⏰ **作业截止提醒** - 智能提醒即将到期的作业（6小时/48小时预警）
- 📱 **微信推送** - 通过 Server酱 将通知推送到微信
- 🔄 **定时运行** - 支持 GitHub Actions 自动定时运行

## 📋 版本说明

- `bot.py` - 基础版本：仅监控交大官网通知
- `bot_pro.py` - 专业版本：监控官网通知 + Canvas 课程更新（推荐用于 GitHub Actions）
- `bot_pro_local.py` - 本地版本：专业版的本地运行版本

## 🚀 快速开始

### 1. 获取必需的 Token

#### Server酱推送 Token (必需)
1. 访问 [Server酱](https://sct.ftqq.com/login)
2. 使用微信扫码登录
3. 复制你的 SendKey (格式: `SCT...`)

#### Canvas Token (可选，仅专业版需要)
1. 登录 [Canvas 平台](https://oc.sjtu.edu.cn)
2. 进入 `账户` -> `设置` -> `批准的集成`
3. 点击 `添加新的访问令牌` 生成 Token

### 2. 本地运行

```bash
# 克隆仓库
git clone https://github.com/gouziman/SJTU-ibot-open.git
cd SJTU-ibot-open

# 安装依赖
pip install requests beautifulsoup4 schedule

# 设置环境变量 (Windows)
set SC_KEY=你的Server酱SendKey
set CANVAS_TOKEN=你的CanvasToken

# 设置环境变量 (Linux/Mac)
export SC_KEY=你的Server酱SendKey
export CANVAS_TOKEN=你的CanvasToken

# 运行基础版本
python bot.py

# 或运行专业版本
python bot_pro.py
```

### 3. GitHub Actions 自动运行

#### 配置 GitHub Secrets
1. Fork 本仓库到你的 GitHub 账号
2. 进入仓库的 `Settings` -> `Secrets and variables` -> `Actions`
3. 点击 `New repository secret` 添加以下密钥：
   - `SC_KEY`: 你的 Server酱 SendKey
   - `CANVAS_TOKEN`: 你的 Canvas Token (可选)

#### 启用 GitHub Actions
1. 进入 `Actions` 标签页
2. 点击 `I understand my workflows, go ahead and enable them`
3. 工作流将每 10 分钟自动运行一次

#### 手动触发运行
在 Actions 页面选择 `SJTU Bot 30min Run` 工作流，点击 `Run workflow` 即可手动触发。

## ⚙️ 配置说明

### 环境变量

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `SC_KEY` | 是 | Server酱推送密钥，用于微信推送 |
| `CANVAS_TOKEN` | 否* | Canvas 平台访问令牌，专业版必需 |

### 定时任务配置

#### bot.py (基础版)
- 每天 08:00、12:00、23:30 运行

#### bot_pro.py (专业版)
- 每 30 分钟运行一次全量巡检

#### GitHub Actions
- 每 10 分钟运行一次（可在 `.github/workflows/run_bot.yml` 中修改）

## 📝 功能详解

### 交大官网通知监控
- 自动抓取上海交通大学官网通知
- 智能去重，避免重复推送
- 推送标题和链接到微信

### Canvas 课程更新监控
- 自动获取所有进行中的课程
- 监控课程公告更新
- 智能作业截止提醒：
  - 48小时预警
  - 6小时紧急提醒
  - 自动跳过已提交作业

### 历史记录管理
- 自动保存已推送内容到 `history.txt`
- GitHub Actions 自动提交历史记录
- 避免重复推送相同内容

## 🛠️ 技术栈

- Python 3.12
- requests - HTTP 请求
- beautifulsoup4 - HTML 解析
- schedule - 定时任务
- GitHub Actions - 自动化运行

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚠️ 注意事项

1. **保护你的 Token** - 不要将 Token 硬编码在代码中或提交到公开仓库
2. **合理使用** - 请勿过于频繁地请求，避免给服务器造成压力
3. **数据安全** - Canvas Token 包含你的个人信息，请妥善保管

## 📮 联系方式

如有问题或建议，欢迎在 GitHub 上提交 Issue。
