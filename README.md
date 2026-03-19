# TEM8Practice

德语专八练习与资料站，当前包含：

- 2016、2017、2018、2019、2021、2022、2023、2025 的词汇语法真题
- 听力、阅读、国情、翻译、写作资料题型
- 本地进度保存、错题本、模考
- 翻译/写作 AI 点评

## 本地启动

在项目根目录运行：

```powershell
.\start.ps1
```

默认会启动本地网关并打开浏览器。常用地址通常是：

```text
http://127.0.0.1:8000
```

如果浏览器缓存了旧前端，按一次 `Ctrl+F5`。

## 题库与进度

- 题库：[data/questions.json](data/questions.json)
- 答案与解析：[data/answer_key.json](data/answer_key.json)
- AI 点评模板：[data/ai_review.template.json](data/ai_review.template.json)
- 用户进度：[data/user_progress.json](data/user_progress.json)

## AI 点评配置

将模板复制为 `data/ai_review.json`，填入 API 信息即可启用。当前代码支持 DeepSeek。

启用后：

- 翻译和写作题会显示 AI 点评入口
- 点击“确定提交”后会自动触发 AI 点评
- 支持“重新提交”“历史记录”“重新 AI 点评”

## Windows 打包

生成安装包：

```powershell
.\build_setup.ps1
```

产物：

- `dist/TEM8Practice.exe`
- `setup/TEM8Practice-Setup.exe`

## macOS 打包

本机是 Windows，macOS 包按现有 GitHub Actions 流程构建。

触发方式：

1. 推送 `main`
2. 推送一个形如 `v2026.03.19-1` 的 tag
3. GitHub Actions 运行 `Release macOS Package`

发布产物：

- `TEM8Practice-macOS-universal2.pkg`
- `TEM8Practice-universal2.app.zip`
- `self-check-universal2.json`

## 数据重建

如果更新了 OCR 或清洗源，可重建当前网站数据：

```powershell
python .\scripts\rebuild_dataset.py
```
