# TEM-8 德语词汇语法刷题站

## 现在怎么启动

### 方式 1：直接起本地网关

```powershell
.\start.ps1
```

默认会：

- 启动本地站点
- 自动挑一个可用端口
- 自动打开浏览器

也可以手动指定：

```powershell
.\start.ps1 -BindHost 127.0.0.1 -Port 8000
.\start.ps1 -NoBrowser
```

### 方式 2：打包成 exe

```powershell
.\build_exe.ps1
```

生成文件：

- `dist/TEM8Practice.exe`

双击 `TEM8Practice.exe` 即可使用。首次运行会把内置的：

- `questions.json`
- `answer_key.json`
- `answer_key.template.json`

释放到 exe 同目录下的 `data` 文件夹，之后你改 `data/answer_key.json` 就会直接生效。

## OCR 与题库刷新

如果你之后换了 PDF，或者要重新抽题：

```powershell
python run.py --extract-only
```

## 当前数据文件

- `data/questions.json`: 题库
- `data/answer_key.json`: 当前实际使用的答案与解析
- `data/answer_key.template.json`: 模板备份
- `data/user_progress.json`: 做题进度
- `logs/server.log`: 服务日志
- `logs/events.jsonl`: 交互事件日志
