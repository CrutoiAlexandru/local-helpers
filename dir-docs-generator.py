import os
import subprocess
import json
from pathlib import Path


def get_directory_structure(root_dir):
    """Get the directory structure starting from root_dir"""
    dir_structure = {}

    for root, dirs, files in os.walk(root_dir):
        # Skip hidden directories and files
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        files = [f for f in files if not f.startswith(".")]

        dirs[:] = [d for d in dirs if not d.startswith("docs")]

        rel_path = os.path.relpath(root, root_dir)
        if rel_path == ".":
            rel_path = ""

        dir_structure[rel_path] = {
            "subdirs": [os.path.join(rel_path, d) for d in dirs] if rel_path else dirs,
            "files": files,
        }

    return dir_structure


def get_directory_content(root_dir, dir_path):
    """Get content information about a specific directory"""
    full_path = os.path.join(root_dir, dir_path) if dir_path else root_dir

    content_info = {
        "path": dir_path if dir_path else "root",
        "files": [],
        "subdirectories": [],
        "file_extensions": set(),
    }

    try:
        for item in os.listdir(full_path):
            if item.startswith("."):
                continue

            item_path = os.path.join(full_path, item)
            if os.path.isfile(item_path):
                content_info["files"].append(item)
                ext = os.path.splitext(item)[1]
                if ext:
                    content_info["file_extensions"].add(ext)
            elif os.path.isdir(item_path):
                content_info["subdirectories"].append(item)

        content_info["file_extensions"] = list(content_info["file_extensions"])
    except PermissionError:
        print(f"Permission denied accessing {full_path}")

    return content_info


def generate_prompt(directory_info, root_dir_name):
    """Generate a prompt for Ollama based on directory information"""
    path = directory_info["path"]
    files = directory_info["files"]
    subdirs = directory_info["subdirectories"]
    extensions = directory_info["file_extensions"]

    prompt = f"""Generate comprehensive documentation for the directory '{path}' in the project '{root_dir_name}'.

Directory Information:
- Path: {path}
- Files: {', '.join(files) if files else 'None'}
- Subdirectories: {', '.join(subdirs) if subdirs else 'None'}
- File extensions present: {', '.join(extensions) if extensions else 'None'}

Please create a detailed markdown documentation that includes:
1. Purpose and functionality of this directory
2. Overview of files and their roles
3. Subdirectories and their purposes
4. How this directory interacts with other parts of the project
5. Any important configuration or setup information
6. Usage examples if applicable

Format the response as clean markdown without any introductory text or code blocks. Start directly with the content."""

    return prompt


def call_ollama(prompt):
    """Call Ollama CLI with the given prompt"""
    try:
        # Call Ollama via CLI
        result = subprocess.run(
            [
                "ollama",
                "run",
                "deepseek-v3.1:671b-cloud",
                "--keepalive",
                "15m",
                "--hidethinking",
            ],
            input=prompt,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Ollama error: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print("Ollama request timed out")
        return None
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None


def save_documentation(docs_dir, dir_path, content):
    """Save the generated documentation to the appropriate location"""
    if dir_path:  # Not root directory
        doc_dir_path = os.path.join(docs_dir, dir_path)
        os.makedirs(doc_dir_path, exist_ok=True)
        doc_file_path = os.path.join(doc_dir_path, "README.md")
    else:  # Root directory
        doc_file_path = os.path.join(docs_dir, "README.md")

    with open(doc_file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Documentation saved: {doc_file_path}")


def main():
    # Configuration
    root_dir = "."  # Current directory
    docs_dir = "./docs"

    # Create docs directory if it doesn't exist
    os.makedirs(docs_dir, exist_ok=True)

    # Get project name from root directory
    root_dir_name = os.path.basename(os.path.abspath(root_dir))

    # Get directory structure
    print("Scanning directory structure...")
    dir_structure = get_directory_structure(root_dir)

    # Process each directory
    for dir_path in dir_structure.keys():
        print(f"\nProcessing directory: {dir_path if dir_path else 'root'}")

        # Get directory content
        dir_info = get_directory_content(root_dir, dir_path)

        # Generate prompt
        prompt = generate_prompt(dir_info, root_dir_name)

        # Call Ollama to generate documentation
        print("Generating documentation with Ollama...")
        documentation = call_ollama(prompt)

        if documentation:
            # Save documentation
            save_documentation(docs_dir, dir_path, documentation)
            print("✓ Documentation generated successfully")
        else:
            print("✗ Failed to generate documentation")

        # Add a small delay to be respectful to the API
        import time

        time.sleep(1)

    print(f"\nDocumentation generation complete! All files saved in {docs_dir}")


if __name__ == "__main__":
    main()
