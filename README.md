# E_Star mdtools

### ✨ 核心功能概览

- **现代化UI**: 采用专业软件设计，拥有图标侧边栏和独立的中心工作区，支持**明暗主题一键切换**。
- **文件迁移**: 轻松将一个或多个 Markdown 文件及其引用的本地图片、远程图片，完整地迁移到新的目标位置。
- **智能重命名**: 强大的**范式重命名**功能，通过 `{original}`, `{num}`, `{date}` 等占位符，随心所欲地将杂乱的文件名变得整齐划一，并支持实时预览。
- **原地处理**: 无需迁移，直接对指定文件夹内的所有 Markdown 文件进行图片路径整理，并能智能跳过已处理过的文件。
- **拖拽操作**: 支持将文件或文件夹直接拖拽到路径输入框，操作行云流水。
- **实时日志**: 内置实时日志系统，所有操作过程清晰可见，便于追踪与调试。

### 🖼️ 软件界面展示

- ### 🚀 安装与运行
  
  本工具使用 Python 开发，运行前请确保您已安装 Python 3.x 环境。
  
  #### 1. 安装依赖库
  
  为了让程序正常运行，您需要安装所有必需的第三方库。请将 `E_star.py` 和 `requirements.txt` 文件放在同一个文件夹下。
  
  然后，打开您的终端（命令提示符或 PowerShell），进入该文件夹，并运行以下命令：
  
  ```
  pip install -r requirements.txt
  ```
  
  这个命令会自动安装 `customtkinter`, `tkinterdnd2`, `requests` 和 `Pillow`。
  
  #### 2. 运行程序
  
  安装完所有依赖后，通过以下命令即可运行本工具：
  
  ```
  python E_star.py
  ```
  
  ### 🛠️ 使用指南
  
  #### 文件迁移
  
  1. 在左侧导航栏点击 **迁移图标** (上下箭头)。
  2. 点击“选择”按钮或直接**拖拽**您的源 Markdown 文件/文件夹到第一个输入框。
  3. 点击“选择”按钮或直接**拖拽**您的目标文件夹到第二个输入框。
  4. 根据需要勾选下方的“处理选项”。
  5. 点击“开始迁移”按钮。
  
  #### 批量重命名
  
  1. 在左侧导航栏点击 **重命名图标** (标签样式)。
  2. 点击“选择文件夹”按钮或直接**拖拽**需要重命名的文件夹到路径输入框。
  3. 在“新文件名范式”输入框中，定义您的命名规则。
  4. 预览框会**实时显示**重命名后的效果。
  5. 确认无误后，点击“应用重命名”按钮。**请注意：此操作不可撤销！**
  
  #### 原地处理
  
  1. 在左侧导航栏点击 **原地处理图标** (带铅笔的文件)。
  2. 点击“选择文件夹并开始处理”按钮。
  3. 选择您需要整理的文件夹，程序会自动处理。
  
  ### 📜 更新日志
  
  - **V6.0 (专业版)**
    - 重构UI为专业级图标侧边栏布局。
    - 新增拖拽操作支持，提升用户体验。
    - 重构批量重命名功能，采用更灵活的“命名范式”系统，并支持实时预览。
    - 修复了多个Bug，提升了稳定性和逻辑健壮性。
  - **V3.0**
    - 增加 Markdown 文件合并功能。
    - 增加整理 Markdown 图片功能。
  - **V1.0**
    - 项目初始版本，实现基本的图片路径处理和重命名。
