# macOS 架构兼容说明

## 这次报错是什么意思

如果弹出：

`你无法打开应用程序 “TEM8Practice”，因为这台 Mac 不支持此应用程序。`

这通常不是“未签名”问题，而是：

- 你的 Mac 是 Intel
- 但下载的是 Apple Silicon `arm64` 版本

或者反过来下载错了架构。

## 现在怎么发最稳

我已经把发布流程改成优先生成 `universal2`：

- `TEM8Practice-macOS-universal2.pkg`
- `TEM8Practice-universal2.app.zip`

`universal2` 目标就是同时兼容：

- Apple Silicon
- Intel Mac

## 你的 Mac 属于哪种

在 Mac 终端执行：

```bash
uname -m
```

结果如果是：

- `arm64`：下载 `arm64` 版本
- `x86_64`：下载 `x86_64` 版本

## 临时解决办法

如果你现在手头只有旧的单架构包：

1. 不要继续装旧包
2. 改用新的 `universal2` 安装包
3. 或先改用浏览器版 / 云端静态页版本

## 备注

- “未知开发者”是签名问题
- “这台 Mac 不支持此应用程序”一般是架构不匹配
