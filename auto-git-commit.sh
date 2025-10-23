#!/bin/bash
set -e

# Help function
show_help() {
    cat << 'EOF'
Usage: auto-git-commit.sh [OPTIONS] [CONTEXT]

Automatically generates git commit messages using AI based on staged changes.

OPTIONS:
    -h, --help          Show this help message and exit

ARGUMENTS:
    CONTEXT             Additional context for the commit message generation

EXAMPLES:
    auto-git-commit.sh                    # Generate commit message without additional context
    auto-git-commit.sh "Fixing login bug" # Generate commit message with context about login bug
    auto-git-commit.sh --help             # Show this help message

FEATURES:
    - Uses Conventional Commits specification
    - Analyzes staged files and git diff
    - Supports optional additional context as direct argument
    - Configurable AI model command
EOF
    exit 0
}

# Parse command line arguments
ADDITIONAL_CONTEXT=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Use -h for help"
            exit 1
            ;;
        *)
            ADDITIONAL_CONTEXT="$1"
            shift
            ;;
    esac
done

git add .

# === CONFIGURATION ===
# Change this to your local AI command.

# Example for Ollama: MODEL="llama3" ; CMD="ollama run $MODEL"
# Example for LM Studio: CMD="curl -s -X POST http://localhost:1234/v1/completions -H 'Content-Type: application/json' -d"
CMD="ollama run deepseek-v3.1:671b-cloud" #qwen2.5-coder:0.5b"

# === COLLECT DATA ===
BRANCH=$(git branch --show-current)
DIFF=$(git diff HEAD)
STAGED_FILES=$(git diff --name-only --cached)

if [ -z "$DIFF" ]; then
  echo "❌ No staged changes to commit."
  exit 1
fi

# === BUILD PROMPT ===
PROMPT=$(cat <<'EOF'
You are an assistant that writes clear and standardized git commit messages using the Conventional Commits specification.

You will receive the git diff, the current branch name, and the list of staged files as input.
Your task is to generate a commit message following these rules:

1. Determine the type of change:
   - feat: new feature
   - fix: bug fix
   - docs: documentation (including README, markdown files, or files with documentation-related names)
   - style: code style (no logic change)
   - refactor: restructuring code (no behavior change)
   - test: adding/updating tests
   - chore: maintenance/tooling

2. Analyze file names to help determine the commit type:
   - Files with names like README, docs, tutorial, guide, explanation → likely docs
   - Files with names containing test, spec, fixture → likely test
   - Files with names containing fix, bug, error, issue → likely fix
   - Files with names containing feat, feature, new, add → likely feat
   - Files with names containing refactor, cleanup, optimize → likely refactor
   - Files with names containing style, format, lint → likely style
   - Files with names containing config, setup, tool, script → likely chore

3. Consider file extensions:
   - .md, .txt, .rst, .adoc → documentation
   - .test.js, .spec.js, _test.go, Test.java → tests
   - Configuration files (.json, .yaml, .yml, .toml, .ini) → chore

4. Format:
<type>: <short summary of the change>
<endline>
<1–3 lines of details or context>

(optional) TICKET-NUMBER (only if present in branch name, otherwise omit)

Rules:
- First line ≤ 72 characters
- Use imperative mood ("add", "fix", "update")
- If the branch name contains a ticket number (SCRUM-ddd, dddd, OBS-ddd, or similar formats), append it as the last line.
- If the ticket number is only made of digits, prefix # to it
- Return only the commit message, no explanations or additional text.
EOF
)

# === COMBINE INPUT ===

INPUT="BRANCH:
$BRANCH

STAGED FILES:
$STAGED_FILES

DIFF:

$DIFF"

# Add additional context if provided
if [ -n "$ADDITIONAL_CONTEXT" ]; then
    INPUT="$INPUT

ADDITIONAL CONTEXT:
$ADDITIONAL_CONTEXT"
fi

# === CALL AI ===

echo "🤖 Generating commit message..."
if [ -n "$ADDITIONAL_CONTEXT" ]; then
    echo "📋 Additional context provided: $ADDITIONAL_CONTEXT"
fi

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