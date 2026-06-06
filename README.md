# 凤梨罐头 FILM LAB

凤梨罐头 FILM LAB 是一个正在独立开发的本地照片处理工作台。目标是为摄影爱好者提供原创预设、基础色调调整、光晕、颗粒、暗角、批量处理和用户自带 LUT 支持。

## 隐私

应用仅监听本机地址，照片和处理结果不会上传到外部服务。运行期间产生的文件保存在独立临时会话目录中，服务退出后清理。

## 当前状态

项目处于早期开发阶段。当前提交只包含经过确认的设计、实施计划和最小 Flask 应用骨架。

## 环境要求

- Python 3.11 或更高版本
- macOS、Windows 或 Linux

## 开发

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest
python run.py
```

Windows 激活环境：

```bat
.venv\Scripts\activate
```

## 独立实现

项目遵循 [CLEAN_ROOM.md](CLEAN_ROOM.md) 中的洁净室边界，不包含旧项目源码、第三方来源不明的预设或样片。

## 许可证

代码采用 [MIT License](LICENSE)。

