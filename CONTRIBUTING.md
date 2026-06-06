# 参与贡献

感谢参与凤梨罐头 FILM LAB。

本项目采用独立实现边界。贡献代码前请先阅读 [CLEAN_ROOM.md](CLEAN_ROOM.md)。

提交代码或资源即表示你确认：

- 你拥有提交内容的版权，或已获得与 MIT 许可证兼容的授权。
- 提交内容不是从未授权项目、商业软件或来源不明的素材中复制而来。
- 新增第三方依赖时，会同步更新 `THIRD_PARTY_NOTICES.md`。
- 不提交无明确分发权的 LUT、XMP、照片、字体或图标。

## 本地开发

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest
python run.py
```

Windows PowerShell 使用 `.\.venv\Scripts\Activate.ps1`。

## 提交要求

- 功能修改应包含对应测试。
- 先运行全量测试和 Python 编译检查。
- 保持提交范围清晰，不混入格式化或无关重构。
- 不提交 `.venv`、缓存、运行期照片和导出文件。
- 用户界面修改应检查桌面与移动端布局。
