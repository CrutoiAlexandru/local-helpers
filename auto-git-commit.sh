#!/bin/bash
set -e

git add .

# === CONFIGURATION ===
# Change this to your local AI command.
# Example for Ollama: MODEL="llama3" ; CMD="ollama run $MODEL"
# Example for LM Studio: CMD="curl -s -X POST http://localhost:1234/v1/completions -H 'Content-Type: application/json' -d"
CMD="ollama run qwen2.5-coder:0.5b"

# === COLLECT DATA ===
BRANCH=$(git branch --show-current)
DIFF=$(git diff HEAD)

if [ -z "$DIFF" ]; then
  echo "❌ No staged changes to commit."
  exit 1
fi

# === BUILD PROMPT ===
PROMPT=$(cat <<'EOF'
You are an assistant that writes clear and standardized git commit messages using the Conventional Commits specification.
You will receive the git diff and the current branch name as input.
Your task is to generate a commit message following these rules:

1. Determine the type of change:
   - feat: new feature
   - fix: bug fix
   - docs: documentation
   - style: code style (no logic change)
   - refactor: restructuring code (no behavior change)
   - test: adding/updating tests
   - chore: maintenance/tooling

2. Format:
<type>: <short summary of the change>
<endline>
<1–3 lines of details or context>

(optional) SCRUM-<number> (only if present in branch name, otherwise omit)

Rules:
- First line ≤ 72 characters
- Use imperative mood (“add”, “fix”, “update”)
- If the branch name contains SCRUM-<number>, append it as the last line.
EOF
)

# === COMBINE INPUT ===
INPUT="BRANCH:
$BRANCH

DIFF:
$DIFF"

# === CALL AI ===
echo "🤖 Generating commit message..."
MESSAGE=$(echo -e "$PROMPT\n\n$INPUT" | $CMD)

# === CLEAN OUTPUT ===
MESSAGE=$(echo "$MESSAGE" | sed '/^```/d' | sed 's/^Output://i' | sed '/^$/N;/^\n$/D')

echo
echo "📝 Commit message preview:"
echo "-------------------------"
echo "$MESSAGE"
echo "-------------------------"
echo

git commit -m "$MESSAGE"