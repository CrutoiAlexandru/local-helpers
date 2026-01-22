# local-helpers
These are some local helpers I use during coding to move faster.

## Prerequisites

### Option 1: GitHub Copilot CLI (Recommended)
Install GitHub Copilot CLI: https://githubnext.com/projects/copilot-cli/
```bash
npm install -g @githubnext/copilot-cli
```
Then authenticate with `copilot auth`.

### Option 2: Ollama (Fallback)
Install Ollama https://ollama.com/download/mac and run `ollama signin`

The scripts will automatically prefer Copilot CLI if available, otherwise fall back to Ollama.

## How to use
Just run `python3 setup.py` and you're good to go.
After that you can run the commands found in alias.txt (e.g. gitc).

## Available Commands

### `gitc` (auto-git-commit.sh)
Automatically generates git commit messages using AI based on staged changes.

```bash
gitc                      # Generate commit message
gitc "context"            # With additional context
gitc -l                   # Use local Ollama model
gitc --help               # Show help
```

**AI Backend Priority:**
1. GitHub Copilot CLI with `gpt-4.1` (if installed)
2. Ollama with `deepseek-v3.1:671b-cloud` (default fallback)
3. Ollama with `gemma3:1b` (with `-l` flag)