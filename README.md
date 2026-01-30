# Rime Auto Deploy

一款基于 Python 的 Rime 输入法自动化部署工具。旨在为 Windows、macOS 和 Linux 用户提供一键式的 Rime 安装、配置及皮肤美化体验。

---

## 🌟 特性

- **全平台支持**: 适配 Windows (小狼毫)、macOS (鼠须管) 及 Linux (fcitx5-rime)。
- **基础配置源可选**: 支持 **雾凇拼音 (Rime-Ice)** 和 **白霜拼音 (Rime-Frost)**。
- **薄荷皮肤适配**: 预设参考自 [Oh-my-rime](https://github.com/Mintimate/oh-my-rime) 的亮/暗模式皮肤，支持系统主题自动切换。
- **自定义配置管理**: 
  - 支持本地 `custom_config/` 目录同步，方便维护个人习惯。
  - **环境感知**: 同步时自动过滤非当前平台的配置文件（如 Windows 下忽略 `squirrel.custom.yaml`）。
  - **方案注入**: 自动在 `default.custom.yaml` 中注入所选输入方案，并为每个方案开启“默认英文”状态。
- **精简直观的模式**: 
  - **Auto**: 适合新手的一键全自动安装流程。
  - **Upgrade**: 快速迭代脚本或拉取上游仓库配置。
  - **Sync**: 一键同步本地自定义配置。
  - **Environment**: 随时修改配置源、方案。
- **状态持久化**: 自动记录偏好，后续操作无需重复选择。

---

## 🚀 快速开始

### 前提条件

- 已安装 [Python](https://www.python.org/) (推荐 3.8+)。
- 推荐使用 [uv](https://github.com/astral-sh/uv) 进行管理。

### 运行步骤

1. **克隆项目**:
   ```bash
   git clone https://github.com/your-username/rime-auto-deploy.git
   cd rime-auto-deploy
   ```

2. **安装依赖并运行**:
   - **使用 uv**:
     ```bash
     uv sync
     uv run main.py
     ```
   - **使用 pip**:
     ```bash
     pip install -r requirements.txt
     python main.py
     

3. **菜单功能详解**:
   - **[1] 自动模式**: 自动完成安装、备份、基础配置下载及自定义同步。
   - **[2] 升级模式**: 检查脚本更新或更新 Rime 词库/基础配置文件。
   - **[3] 同步配置**: 修改本地 `custom_config/` 后，使用此项快速推送到 Rime 目录并重新部署。
   - **[4] 环境配置**: 重新选择配置源（雾凇/白霜）或切换输入方案（全拼/双拼等）。

---

## 🛠️ 自定义配置

您可以将自己的 `.yaml` 配置文件放入 `custom_config/` 目录。

- **皮肤设置**: 修改 `weasel.custom.yaml` (Windows) 或 `squirrel.custom.yaml` (macOS)。脚本会自动根据您的系统选择性同步。
- **个人习惯**: 修改 `default.custom.yaml` (脚本会自动为您同步并注入选定的输入方案)。
- **默认英文**: 脚本会自动为每个启用的方案生成 `.custom.yaml` 并注入 `switches/@0/reset: 1`，确保初始切换到该方案时为英文模式。

---

## 🤝 致谢

本项目在开发过程中参考并集成了以下优秀开源项目：

- **部署形式**: 参考自 [Mark24Code/rime-auto-deploy](https://github.com/Mark24Code/rime-auto-deploy)。
- **配置源**: [iDvel/rime-ice (雾凇拼音)](https://github.com/iDvel/rime-ice) 及 [gaboolic/rime-frost (白霜拼音)](https://github.com/gaboolic/rime-frost)。
- **视觉美化**: 配色样式参考自 [rime/weasel示例](https://github.com/rime/weasel/wiki/%E7%A4%BA%E4%BE%8B)。

---

## 📄 开源协议

[MIT License](LICENSE)
