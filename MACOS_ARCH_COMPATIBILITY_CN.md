# macOS 架构兼容说明

## 这次报错是什么意思

如果弹出：

`你无法打开应用程序 “TEM8Practice”，因为这台 Mac 不支持此应用程序。`

这通常不是“未签名”问题，而是：

- 你的 Mac 是 Intel
- 但下载的是 Apple Silicon `arm64` 版本

或者反过来下载错了架构。

## 以后应该怎么选安装包

我们现在会分别发布两套包：

- `TEM8Practice-macOS-arm64.pkg`
- `TEM8Practice-macOS-x86_64.pkg`

以及两套 app 压缩包：

- `TEM8Practice-arm64.app.zip`
- `TEM8Practice-x86_64.app.zip`

## 你的 Mac 属于哪种

在 Mac 终端执行：

```bash
uname -m
```

结果如果是：

- `arm64`：下载 `arm64` 版本
- `x86_64`：下载 `x86_64` 版本

## 临时解决办法

如果你现在手头只有错误架构的包：

1. 不要继续装这个包
2. 等新的双架构 release
3. 或先改用浏览器版 / 云端静态页版本

## 备注

- “未知开发者”是签名问题
- “这台 Mac 不支持此应用程序”一般是架构不匹配
