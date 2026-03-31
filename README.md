# Lock Pomodoro

一个面向 macOS 的极简菜单栏番茄钟，用来把专注和休息强制切开。

长时间工作时，人很容易忘记停下来。这个应用的核心设计就是把番茄钟放到菜单栏里，尽量减少存在感；而在工作阶段结束时主动尝试锁屏，打断惯性，让你真正离开屏幕休息几分钟。

## 设计目标

- 常驻菜单栏，界面简单，不干扰正常工作
- 让工作、短休息、长休息自然循环
- 在工作阶段结束时尝试锁屏，减少“知道该休息但继续工作”的情况
- 所有常用配置都能直接在窗口里修改并保存

## 功能特点

- 可配置工作时长、短休息、长休息、每轮番茄数
- 支持开始、暂停、重置、隐藏和退出
- 工作阶段结束时自动尝试锁屏
- 即使屏幕已经锁定，计时也会继续按真实时间推进
- 自动记住上一次保存的配置

## 使用方式

### 本地运行

```bash
uv sync
uv run lock-pomodoro
```

程序启动后会显示控制窗口，并在菜单栏放置一个计时器图标。

### 打包应用

```bash
uv sync --extra build
uv run pyinstaller lock_pomodoro.spec
```

产物位于 `dist/Lock Pomodoro.app`。

## 运行说明

- 锁屏优先调用 `login.framework` 的 `SACLockScreenImmediate`
- 如果该方式失败，会回退到 `osascript`
- 未签名构建在其他 Mac 上首次打开时，通常需要手动放行

## 开发说明

### 项目结构

- `src/lock_pomodoro/app.py`：AppKit 窗口、菜单栏、配置读写、计时回调
- `src/lock_pomodoro/engine.py`：纯计时状态机，使用阶段结束时间戳推进
- `src/lock_pomodoro/lockscreen.py`：锁屏实现与回退策略
- `tests/`：`unittest` 测试
- `assets/`：图标与菜单栏资源

### 测试

```bash
uv run python -m unittest discover -s tests
```

当前测试覆盖计时状态机和锁屏调用回退逻辑。

### 开发约定

- 只修改 `src/`、`tests/` 和文档
- `build/`、`dist/` 是生成目录，不要手改
- 提交前至少跑一次测试
