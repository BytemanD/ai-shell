# AI-Shell

AI-powered shell command generator - 用自然语言生成终端命令

## 特性

- **自然语言转命令**: 将你的意图描述转换为可执行的终端命令
- **多模型支持**: 支持 OpenAI 兼容的 API，可配置多种 AI 提供商
- **交互模式**: 支持实时对话，随时调整命令
- **流式输出**: 实时显示 AI 思考过程和输出结果
- **安全确认**: 执行命令前会要求用户确认

## 安装

```bash
pip install -i https://test.pypi.org/simple/ ai-shell
```

## 快速开始

### 配置 API Key

在 `~/.config/ai-shell/ai-shell.toml` 中配置你的 API:

```toml
use_provider = "alibaba"
[[providers]]
name = "alibaba"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
model = "qwen-plus"
api_key = "your-api-key"
```

其他配置
```toml

[[providers]]
# 启用思考模式
extra_body = {enable_thinking = true}


```

### 使用方式

**交互模式** - 持续对话:

```bash
ai-shell chat
```

**单次执行** - 执行单个命令:

```bash
ai-shell run "查找当前目录下所有大于 100MB 的文件"
```

**列出可用模型**:

```bash
ai-shell list-model
```

## 命令

| 命令 | 说明 |
|------|------|
| `ai-shell chat` | 进入交互式对话模式 |
| `ai-shell run <指令>` | 直接执行单条命令 |
| `ai-shell list-model` | 列出可用的 AI 模型 |
| `ai-shell config list` | 显示当前配置 |

### 交互模式命令

| 命令 | 说明 |
|------|------|
| `/messages` | 显示对话历史 |
| `/actions` | 显示可用操作 |

### 选项

- `-y, --yes`: 跳过确认直接执行
- `-v, --verbose`: 增加日志详细程度 (-v, -vv, -vvv)

## 项目结构

```
ai-shell/
├── src/ai_shell/
│   ├── cmd/           # CLI 命令入口
│   ├── common/        # 配置管理
│   └── core/          # 核心 AI 功能
├── tests/             # 测试文件
└── pyproject.toml     # 项目配置
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE)
