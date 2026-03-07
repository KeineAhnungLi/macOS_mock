# macOS 打包步骤

这是给不会用 Codex 的同学直接照着做的版本。

## 1. 把交接包传到 Mac

把这个文件传到 Mac：

- `TEM8Practice-macos-handoff.zip`

双击解压，得到一个目录，例如：

- `~/Desktop/TEM8Practice-macos-handoff`

## 2. 打开终端

在 Mac 上打开：

- `Terminal`

进入解压后的目录，例如：

```bash
cd ~/Desktop/TEM8Practice-macos-handoff
```

## 3. 先检查构建环境

先运行：

```bash
xcode-select -p
python3 --version
```

要求：

- `python3` 版本至少 `3.10`
- `xcode-select -p` 能正常输出路径

如果 `xcode-select -p` 报错，就先执行：

```bash
xcode-select --install
```

如果 `python3` 太旧或没有，就先安装 Python 3.10+。

## 4. 直接一键构建

运行：

```bash
chmod +x build_macos_all.sh
./build_macos_all.sh
```

它会自动做这些事：

1. 检查 macOS 构建依赖
2. 构建 `.app`
3. 跑一次程序自检
4. 再构建 `.pkg`

## 5. 期望产物

构建成功后，应该看到：

- `release/macos/dist/TEM8Practice.app`
- `release/macos/TEM8Practice-macOS.pkg`

## 6. 可选验证

先直接打开 app：

```bash
open release/macos/dist/TEM8Practice.app
```

如果系统提示来源不明，可以试：

```bash
xattr -dr com.apple.quarantine release/macos/dist/TEM8Practice.app
open release/macos/dist/TEM8Practice.app
```

如果要测试安装包：

```bash
sudo installer -pkg release/macos/TEM8Practice-macOS.pkg -target /
open -a TEM8Practice
```

## 7. 打包完成后发回来的东西

请同学把下面两样发回来：

- `release/macos/dist/TEM8Practice.app`
- `release/macos/TEM8Practice-macOS.pkg`

如果中间报错，请把终端完整报错一起发回来。
