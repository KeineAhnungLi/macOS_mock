# macOS 用户使用说明

## 现在怎么拿到安装包

现在已经有一份成功的 macOS 构建产物：

- Actions run: `https://github.com/KeineAhnungLi/macOS_mock/actions/runs/22804417745`
- artifact 名称: `TEM8Practice-macos`

下载后，压缩包里会有：

- `TEM8Practice.app.zip`
- `TEM8Practice-macOS.pkg`
- `self-check.json`

## 推荐安装方式

优先使用 `TEM8Practice-macOS.pkg`：

1. 下载 `TEM8Practice-macos` artifact。
2. 解压后双击 `TEM8Practice-macOS.pkg`。
3. 如果系统提示来自未知开发者：
   - 在 Finder 里右键安装包，选择“打开”。
   - 或去“系统设置 -> 隐私与安全性”，点击“仍要打开”。
4. 安装完成后，在“应用程序”里打开 `TEM8Practice`。

## 不安装也能用

如果不想走 pkg，也可以：

1. 解压 `TEM8Practice.app.zip`
2. 把 `TEM8Practice.app` 拖进“应用程序”
3. 第一次右键 `TEM8Practice.app`，选择“打开”

## 第一次启动后会发生什么

- 程序会把运行数据写到：
  - `~/Library/Application Support/TEM8Practice`
- 题库、答案模板、日志都会放在这个目录下
- 做题进度也会保存在这里

## 浏览器依赖

- 程序会检查 Chrome
- 如果没有 Chrome，程序仍然可以使用，会自动回退到默认浏览器

## 如果被 Gatekeeper 拦住

如果右键打开仍然不行，在终端执行：

```bash
xattr -dr com.apple.quarantine /Applications/TEM8Practice.app
```

如果你没有装到“应用程序”，就把路径改成实际的 `.app` 路径。

## 以后正式发版怎么拿

仓库已经有单独的发布工作流：

- workflow: `Release macOS Package`

它跑完之后，用户可以直接去 GitHub 的 `Releases` 页面下载，不必再去 `Actions` 里拿 artifact。
