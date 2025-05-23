# PDF Logo 删除工具

一个简单易用的 macOS 脚本，用于从 PDF 文件中提取并删除 Logo 图像。通过交互式界面，您可以轻松选择要删除的 Logo，无需复杂的命令行操作。

## 功能特点

- 自动提取 PDF 中的所有图像组件
- 合并重复图像，便于识别 Logo
- 交互式界面选择要删除的 Logo
- 生成无 Logo 的新 PDF 文件
- 保存提取的图像供参考
- 彩色提示信息，用户友好

## 安装步骤

### 1. 安装依赖库

确保您的系统已安装 Python 3 和以下依赖库：

```bash
pip3 install pymupdf pillow tqdm
```

### 2. 下载脚本

将以下两个文件下载到同一目录：

- `remove_pdf_logo.command` - 主脚本文件
- `pdf_logo_remover.py` - Python 执行文件

## 使用方法

### 方式一：双击直接运行（推荐）

1. 右键点击 `remove_pdf_logo.command` 文件
2. 选择「打开方式」→「终端」
3. 按照终端提示输入参数

### 方式二：通过终端命令运行

1. 打开终端
2. 切换到脚本所在目录：
   ```bash
   cd /path/to/script/directory
   ```
3. 赋予执行权限：
   ```bash
   chmod +x remove_pdf_logo.command
   ```
4. 运行脚本：
   ```bash
   ./remove_pdf_logo.command
   ```

### 交互流程

1. **输入 PDF 文件路径**：
   - 可直接拖入 PDF 文件到终端窗口

2. **输入输出文件路径**：
   - 默认使用原文件名添加 `_no_logo` 后缀

3. **输入保存图像的目录**：
   - 脚本会将提取的图像保存至此目录

4. **选择要删除的 Logo**：
   - 查看保存的图像，输入对应编号选择 Logo
   - 支持选择多个编号（用逗号分隔）

5. **确认操作**：
   - 确认后脚本会处理 PDF 并生成结果文件

## 示例运行

```
=== PDF Logo 删除工具 ===

请输入PDF文件路径: /Users/yourname/Documents/sample.pdf
请输入输出文件路径 (默认: /Users/yourname/Documents/sample_no_logo.pdf): 
请输入保存提取图像的目录 (默认: ./pdf_images): 

参数确认:
  输入PDF: /Users/yourname/Documents/sample.pdf
  输出PDF: /Users/yourname/Documents/sample_no_logo.pdf
  图像目录: ./pdf_images

是否继续? (y/n): y

开始处理PDF...

以下是PDF中提取的图像组件：
1. 图像 #123 (200x100px, 128.5KB)
   出现次数: 3, 所在页面: 1,3,5
   保存路径: ./pdf_images/image_1.png
--------------------------------------------------
2. 图像 #456 (150x50px, 45.2KB)
   出现次数: 1, 所在页面: 2
   保存路径: ./pdf_images/image_2.png
--------------------------------------------------

请输入要作为Logo删除的图像编号（用逗号分隔，如 1,3,5），或输入 'all' 删除全部，输入 'q' 退出: 1

您选择了以下 1 个图像组件作为Logo:
1. 图像 #123 (200x100px), 出现 3 次, 页面: 1,3,5

确定要从PDF中删除这些图像吗？(y/n): y

开始从PDF中删除 1 个图像组件...
[███████████████████████████████████████] 100% | 页面处理进度 | 5/5 [00:05<00:00,  1.02s/页]

正在保存修改后的PDF...

处理成功!
- 输入文件: /Users/yourname/Documents/sample.pdf
- 输出文件: /Users/yourname/Documents/sample_no_logo.pdf
- 删除图像数量: 成功删除 1/1 个图像组件

是否打开保存图像的目录? (y/n): y
```

## 常见问题

### 1. 脚本无法运行，提示权限不足

执行以下命令赋予脚本执行权限：

```bash
chmod +x remove_pdf_logo.command
```

### 2. 提示 "无法验证" 错误

这是 macOS 的安全机制阻止未签名应用运行。您可以：

1. 打开「系统偏好设置」→「安全性与隐私」
2. 在「通用」选项卡中点击「仍要打开」
3. 再次尝试运行脚本

或通过终端命令绕过验证：

```bash
sudo xattr -rd com.apple.quarantine /path/to/remove_pdf_logo.command
```

### 3. 运行时提示缺少依赖库

确保已安装所有必要的 Python 库：

```bash
pip3 install pymupdf pillow tqdm
```

### 4. 提取的图像中没有找到 Logo

可能原因：
- Logo 是矢量图形而非位图图像
- Logo 被嵌入为文本
- Logo 与其他内容合并为一个图像

## 技术支持

如有任何问题或建议，请联系作者：wljimmy@hotmail.com

## 许可证

本项目采用 MIT 许可证 - 详情见 [LICENSE](LICENSE) 文件。
