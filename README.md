# DirTidy 🧹

[中文](README.md) | **English**

**让下载文件夹自己变干净。** 监控指定文件夹，按扩展名自动把文件归类到子文件夹，随时一键撤销。

[![CI](https://github.com/yund229/DirTidy/actions/workflows/ci.yml/badge.svg)](https://github.com/yund229/DirTidy/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

![demo](https://cdn.jsdelivr.net/gh/yund229/DirTidy@main/assets/demo.gif)

## 特性

- **零依赖** — 纯 Python 标准库，无 watchdog、无 yaml，装完即用
- **自动归类** — 图片 / 文档 / 压缩包 / 安装程序 / 视频 / 音频 / 字体 / 代码 / 种子，9 大类开箱即用
- **规则可定制** — `--dump-rules` 导出默认规则，编辑成自己的 JSON 再用 `--rules` 加载
- **dry-run** — `--dry-run` 先看看会怎么动，满意再执行
- **一键撤销** — 每次整理都写入 JSONL 日志，`--undo` 撤销上一批，`--undo-all` 全部还原
- **重名不覆盖** — 自动重命名为 `文件 (1).jpg`、`文件 (2).jpg`
- **跨平台** — Windows / macOS / Linux 行为一致，还提供免安装的 Windows exe
- **65 个单元测试** — CI 矩阵覆盖 3.9 / 3.11 / 3.13 × Ubuntu / Windows

## 安装

**方式一：pip 安装（推荐）**

```bash
pip install git+https://github.com/yund229/DirTidy.git
```

**方式二：下载免安装 exe**

在 [Releases](https://github.com/yund229/DirTidy/releases) 页面下载 `DirTidy.exe`（Windows，无需装 Python）。

## 快速上手

```bash
# 整理一次下载文件夹
dirtidy ~/Downloads

# 先预览将要发生的移动，不实际执行
dirtidy ~/Downloads --dry-run

# 常驻监控：有新文件就自动归类（Ctrl+C 停止）
dirtidy ~/Downloads --watch

# 撤销最近一批整理 / 撤销全部
dirtidy ~/Downloads --undo
dirtidy ~/Downloads --undo-all
```

也可以不安装直接用模块方式运行：

```bash
python -m dirtidy ~/Downloads --watch --dry-run
```

## 自定义规则

默认规则按扩展名分为 9 类（顺序即优先级，先匹配先生效）：

| 分类 | 扩展名示例 |
|------|-----------|
| Images | .jpg .png .gif .webp .svg .heic |
| Documents | .pdf .docx .xlsx .pptx .txt .md .epub |
| Archives | .zip .rar .7z .tar.gz .iso |
| Installers | .exe .msi .dmg .apk |
| Videos | .mp4 .mkv .mov .webm |
| Audio | .mp3 .flac .wav .m4a |
| Fonts | .ttf .otf .woff2 |
| Code | .py .js .ts .html .json .sh |
| Torrents | .torrent |

导出默认规则、修改、加载：

```bash
dirtidy --dump-rules myrules.json     # 导出默认规则
# 编辑 myrules.json：删掉不要的分类、加上自己的，比如
# "学习资料": [".pptx", ".epub"]
dirtidy ~/Downloads --rules myrules.json
```

说明：`--rules` 传入的 JSON **完全取代**默认规则（不合并），所以建议从 `--dump-rules` 开始改。没有匹配到任何规则的文件会留在原地不动，`.dirtidy.jsonl` 日志和点开头的隐藏文件也会被跳过。

## 工作原理

1. **扫描**：遍历目标文件夹顶层文件（不递归子文件夹）
2. **分类**：按扩展名查规则表，得到目标子文件夹
3. **冲突处理**：目标已存在则自动改名 `name (1).ext`
4. **移动**：执行移动并把 `src → dst` 追加进 JSONL 日志
5. **撤销**：倒序回放日志把文件移回原处，若原位置已有同名文件则改名恢复

监控采用目录轮询（默认 3 秒），不依赖平台特定的文件系统事件 API，所以在三大平台上行为完全一致，测试也更可靠。

## 项目结构

```
dirtidy/
├── rules.py     # 分类规则与加载
├── mover.py     # 规划 / 执行 / 日志 / 撤销
├── watcher.py   # 轮询监控
├── cli.py       # 命令行入口
└── __main__.py
tests/           # 65 个单元测试
```

## License

[MIT](LICENSE)
