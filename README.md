# ShellGPT Safety Edition

> 基于开源项目 [TheR1D/shell_gpt](https://github.com/TheR1D/shell_gpt) 的二次开发版本，新增 **高风险 Shell 命令安全检测机制**。

ShellGPT 是一个基于大语言模型的命令行助手，可以将用户的自然语言需求转换成 Shell 命令、代码片段或解释说明。本项目在原有功能基础上，重点增强了 Shell 命令执行前的安全性。

## Project Highlights

- **Natural Language to Shell Command**
  - 用户输入自然语言，系统生成对应 Shell 命令。

- **High-Risk Command Detection**
  - 本地静态分析生成的 Shell 命令，识别高风险操作。

- **Risk Explanation**
  - 对危险命令给出明确风险原因。

- **Secondary Confirmation**
  - 高风险命令执行前要求用户再次确认。

- **REPL Protection**
  - 在 Shell REPL 模式下同样进行安全检查。

- **Function Calling Protection**
  - 对 LLM function calling 中的 Shell 执行入口增加默认阻断机制。

## What Was Improved

原始 ShellGPT 已经支持生成并执行 Shell 命令，但如果模型生成了危险命令，例如：

```bash
rm -rf /
```

或者：

```powershell
Remove-Item -Recurse -Force
```

用户可能在未充分理解风险的情况下执行。  
本项目新增了一个本地 Shell 安全检测模块，在命令执行前识别危险操作并给出提示。

## Risk Rules

当前安全模块可以识别的典型风险包括：

- **Destructive deletion**
  - 例如 `rm -rf`、`Remove-Item -Recurse -Force`

- **Disk or filesystem operation**
  - 例如 `dd`、`mkfs`、`fdisk`、`diskpart`、`format`

- **Remote script execution**
  - 例如 `curl ... | bash`、`wget ... | sh`

- **System shutdown or reboot**
  - 例如 `shutdown`、`reboot`、`poweroff`

- **Account removal**
  - 例如 `userdel`、`deluser`

- **Recursive permission change**
  - 例如 `chmod -R`、`chown -R`

## Modified Files

本项目主要修改和新增了以下文件：

```text
sgpt/shell_safety.py
sgpt/app.py
sgpt/config.py
sgpt/handlers/repl_handler.py
sgpt/llm_functions/common/execute_shell.py
tests/test_shell_safety.py
.gitignore
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/cliff677/shell_gpt_experiment1.git
cd shell_gpt_experiment1
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install the project

```bash
pip install -e .
```

## API Configuration

ShellGPT uses an OpenAI-compatible API. You can use OpenAI, DeepSeek, OpenRouter, Groq, or other compatible providers.

### DeepSeek example

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your-api-key"
$env:API_BASE_URL="https://api.deepseek.com"
$env:DEFAULT_MODEL="deepseek-chat"
```

Linux / macOS:

```bash
export OPENAI_API_KEY="your-api-key"
export API_BASE_URL="https://api.deepseek.com"
export DEFAULT_MODEL="deepseek-chat"
```

> Do not commit API keys to GitHub.

## Usage

### Show help

```bash
sgpt --help
```

### Generate a safe shell command

```bash
sgpt -s "list all files in the current directory"
```

Example behavior:

```text
dir
[E]xecute, [M]odify, [D]escribe, [A]bort:
```

Safe commands are not blocked.

### Detect a high-risk command

```bash
sgpt -s "recursively force delete the temp directory"
```

If the generated command is risky, ShellGPT will show a warning:

```text
Shell safety check: HIGH RISK command detected.
[HIGH] Destructive deletion: Detected recursive or forced deletion that can irreversibly remove files.
[E]xecute, [M]odify, [D]escribe, [A]bort:
```

If the user chooses to execute it, a second confirmation is required:

```text
High-risk command detected. Execute this command anyway? [y/N]:
```

### Disable shell safety check

```bash
sgpt -s "recursively force delete the temp directory" --no-shell-safety
```

This disables the local shell safety check for the current command.

### Shell REPL mode

```bash
sgpt --repl temp --shell
```

In Shell REPL mode, typing `e` to execute the generated command will also trigger the safety check.

### Describe a shell command

```bash
sgpt -d "tar -xzvf archive.tar.gz"
```

### Generate code

```bash
sgpt -c "write a Python function to calculate Fibonacci numbers"
```

## Demo Script

Recommended commands for a short demo video:

```bash
sgpt --help
sgpt -s "list all files in the current directory"
sgpt -s "recursively force delete the temp directory"
sgpt -s "recursively force delete the temp directory" --no-shell-safety
sgpt --repl temp --shell
```

Recommended explanation:

- **Normal command**
  - The original ShellGPT feature still works.

- **Dangerous command**
  - High-risk commands are detected before execution.

- **Secondary confirmation**
  - The user must confirm again before executing a dangerous command.

- **Configurable behavior**
  - Safety checks can be disabled with `--no-shell-safety`.

- **REPL protection**
  - REPL command execution is also protected.

## Tests

Run the shell safety tests:

```bash
python -c "import os, sys, pytest; os.environ['OPENAI_API_KEY']='test'; sys.exit(pytest.main(['tests/test_shell_safety.py','-q']))"
```

Expected result:

```text
7 passed
```

The tests cover:

- High-risk command detection
- Medium-risk command detection
- Shell mode secondary confirmation
- Disabling shell safety
- REPL mode safety check
- Function calling high-risk command blocking
- Safe command execution

## Project Structure

```text
shell_gpt_experiment1/
├── sgpt/
│   ├── app.py
│   ├── config.py
│   ├── shell_safety.py
│   ├── handlers/
│   │   └── repl_handler.py
│   └── llm_functions/
│       └── common/
│           └── execute_shell.py
├── tests/
│   └── test_shell_safety.py
├── pyproject.toml
└── README.md
```

## Technical Design

The safety enhancement is implemented as a separate module:

```text
sgpt/shell_safety.py
```

The module provides:

- Rule-based local static analysis
- Risk severity classification
- Human-readable risk report
- Secondary confirmation helper
- Blocking message for function calls

The module is integrated into three execution paths:

- **CLI shell mode**
  - `sgpt/app.py`

- **Shell REPL mode**
  - `sgpt/handlers/repl_handler.py`

- **LLM function calling**
  - `sgpt/llm_functions/common/execute_shell.py`

## Configuration

New configuration items:

```text
SHELL_SAFETY=true
ALLOW_HIGH_RISK_SHELL_FUNCTIONS=false
```

Meaning:

- **`SHELL_SAFETY`**
  - Enables or disables local shell safety checks by default.

- **`ALLOW_HIGH_RISK_SHELL_FUNCTIONS`**
  - Controls whether high-risk commands are allowed in LLM function calling.

## Background

This project was developed as a source-code analysis and improvement experiment based on ShellGPT.

The original project:

```text
https://github.com/TheR1D/shell_gpt
```

This repository keeps the original project history and adds one focused improvement:

```text
High-risk Shell command safety checking before execution.
```

## License

This project follows the original project's MIT License.

## Acknowledgement

Thanks to the original ShellGPT project and its contributors:

- [TheR1D/shell_gpt](https://github.com/TheR1D/shell_gpt)
