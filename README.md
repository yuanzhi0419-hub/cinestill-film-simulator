# 凤梨罐头 FILM LAB

凤梨罐头 FILM LAB 是由 `yuanzhi0419-hub` 独立开发的本地照片处理工作台。它提供原创胶片预设、基础色调调整、光晕、颗粒、暗角、批量处理和用户自带 `.cube` LUT 支持。

## 隐私

默认启动命令只监听 `127.0.0.1`。应用不调用云端图像服务，也不会主动把照片、LUT 或处理结果上传到外部服务器。

运行期间的输入、预览、导出和 LUT 保存在操作系统临时目录中的独立会话文件夹。应用正常退出时会清理当前会话；如果进程异常终止，可以手动删除系统临时目录中的 `pineapple-film-lab` 文件夹。

## 功能与格式

- 输入：JPG/JPEG、PNG、WebP、TIFF，以及 rawpy 支持的常见 RAW，如 DNG、NEF、CR2、CR3、ARW、RAF、RW2、ORF。
- 输出：单张照片导出为 JPEG；多张照片导出为包含 JPEG 的 ZIP。
- 调整：曝光、对比度、高光、阴影、色温、饱和度、光晕、颗粒和暗角。
- 预设：夜行、清晨、自然负片、柔雾和黑白纪实。
- 对比：原片、效果和可拖动分割对比。
- 队列：多图参数管理、应用到全部、任务进度、取消、重试和下载。
- LUT：导入用户自己的 3D `.cube` 文件，不捆绑第三方 LUT。

## 环境要求

- Python 3.11 或更高版本
- macOS、Windows 或 Linux

## macOS / Linux 安装

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
```

浏览器打开 [http://127.0.0.1:5000](http://127.0.0.1:5000)。如果 `5000` 端口被占用，可使用：

```bash
FLASK_APP=run.py flask run --host 127.0.0.1 --port 5001
```

## macOS 快捷启动

项目提供无需打开终端的桌面启动器。首次安装依赖后，运行一次：

```bash
./scripts/build_macos_launcher.sh
```

脚本会生成两个带银色相机图标的“凤梨罐头 FILM LAB.app”：

- 项目内：`launcher/凤梨罐头 FILM LAB.app`
- 桌面：`~/Desktop/凤梨罐头 FILM LAB.app`

之后双击任意一个图标即可在后台启动服务并自动打开浏览器。重复双击不会重复启动服务，只会打开现有页面。

图标源文件保存在 `assets/macos/camera-icon.png`，macOS 图标文件保存在 `assets/macos/camera-icon.icns`。

后台服务默认使用 [http://127.0.0.1:7860](http://127.0.0.1:7860)，日志保存在：

```text
~/Library/Logs/PineappleFilmLab/server.log
```

如果项目目录发生移动，请重新运行 `./scripts/build_macos_launcher.sh` 生成启动器。

## Windows 安装

在 PowerShell 中运行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
```

然后打开 [http://127.0.0.1:5000](http://127.0.0.1:5000)。

## 使用流程

1. 点击“添加照片”，或把一张或多张照片拖入工作台。
2. 在左侧选择预设；移动端先点击“预设”标签。
3. 在右侧调整参数；移动端先点击“参数”标签。
4. 使用“原片 / 效果 / 对比”切换查看方式；对比模式可拖动中间分割线。
5. 需要统一批量风格时，点击“应用到全部”。
6. 可选：点击“LUT”导入自己拥有使用权的 `.cube` 文件。
7. 点击“导出”，等待底部任务进度完成。
8. 点击“下载”。单张照片得到 JPEG，多张照片得到 ZIP。

重新上传不会覆盖原文件。移除照片只会清理当前应用会话中的临时副本。

## 用户 LUT

本仓库不附带 LUT、XMP 或样片。导入 LUT 前，请确认你拥有该文件的使用和处理权限。应用不会替用户判断第三方 LUT 的许可证，也不会把导入的 LUT 重新分发。

## Docker

构建镜像：

```bash
docker build -t pineapple-film-lab .
```

仅映射到本机地址运行：

```bash
docker run --rm -p 127.0.0.1:7860:7860 pineapple-film-lab
```

浏览器打开 [http://127.0.0.1:7860](http://127.0.0.1:7860)。

## 测试

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -v
PYTHONPYCACHEPREFIX=/tmp/pineapple-film-lab-pycache \
  python -m compileall -q pineapple_film_lab tests
```

Windows 使用 `.\.venv\Scripts\Activate.ps1` 激活环境；编译检查可直接运行：

```powershell
python -m compileall -q pineapple_film_lab tests
```

## 独立实现与第三方依赖

项目遵循 [CLEAN_ROOM.md](CLEAN_ROOM.md) 中的独立实现边界，不包含先前项目源码、未授权媒体、第三方来源不明的预设、LUT 或样片。依赖及其许可证见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 许可证

代码采用 [MIT License](LICENSE)，版权归 `yuanzhi0419-hub` 所有。
