import os
import re
import shutil
from pathlib import Path


class ShellConfigManager:
    def __init__(self):
        self.home_dir = Path.home()
        self.bashrc_path = self.home_dir / ".bashrc"
        self.zshrc_path = self.home_dir / ".zshrc"
        self.script_dir = Path(__file__).parent
        self.markers = {"start": "## local-helpers", "end": "## local-helpers"}

        # Load aliases from alias.txt file
        self.aliases = self.load_aliases_from_file()

    def load_aliases_from_file(self):
        """Load aliases from alias.txt file"""
        alias_file = self.script_dir / "alias.txt"
        aliases = {}

        if not alias_file.exists():
            print(f"Warning: alias.txt file not found at {alias_file}")
            return aliases

        try:
            with open(alias_file, "r") as f:
                for line_number, line in enumerate(f, 1):
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Handle function definitions (containing (){)
                    if "(){" in line:
                        # For function definitions, use the entire line as the command
                        # Extract alias name (everything before (){)
                        alias_name = line.split("(){", 1)[0].strip()
                        aliases[alias_name] = line
                    elif "=" in line:
                        # Split on the first = only
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            alias_name = parts[0].strip()
                            command = parts[1].strip()
                            # Remove surrounding quotes if present
                            if (command.startswith('"') and command.endswith('"')) or (
                                command.startswith("'") and command.endswith("'")
                            ):
                                command = command[1:-1]
                            aliases[alias_name] = command
                        else:
                            print(
                                f"Warning: Invalid alias format on line {line_number}: {line}"
                            )
                    else:
                        print(
                            f"Warning: Invalid alias format on line {line_number}: {line}"
                        )

        except Exception as e:
            print(f"Error reading alias.txt: {e}")

        # Validate that we loaded some aliases
        if not aliases:
            print("Warning: No valid aliases found in alias.txt")
        else:
            print(f"Loaded {len(aliases)} aliases from alias.txt")

        return aliases

    def get_script_absolute_path(self, script_name):
        """Get the absolute path to a script in this repository"""
        path = self.script_dir / script_name
        return str(path).replace("\\", "/")

    def generate_alias_content(self):
        """Generate the alias section content"""
        content = [self.markers["start"]]
        content.append("# Aliases for local helper scripts")
        content.append("# Generated automatically by setup.py")
        content.append("")

        for alias_name, command in self.aliases.items():
            # Check if command is a function definition (contains (){)
            if "(){" in command:
                # For function definitions, use the complete definition
                content.append(command)
            else:
                # Check if command references a script file
                if command.endswith(".sh") or command.endswith(".py"):
                    script_path = self.get_script_absolute_path(command)
                    if command.endswith(".sh"):
                        content.append(f'alias {alias_name}="{script_path}"')
                    elif command.endswith(".py"):
                        content.append(f'alias {alias_name}="python3 {script_path}"')
                else:
                    # For regular commands, create an alias
                    content.append(f'alias {alias_name}="{command}"')

        content.append("")
        content.append(self.markers["end"])
        return "\n".join(content)

    def find_existing_section(self, content):
        """Find the existing local-helpers section in the content"""
        pattern = re.compile(
            rf'{re.escape(self.markers["start"])}.*?{re.escape(self.markers["end"])}',
            re.DOTALL,
        )
        match = pattern.search(content)
        return match

    def remove_existing_section(self, content):
        """Remove the existing local-helpers section"""
        pattern = re.compile(
            rf'{re.escape(self.markers["start"])}.*?{re.escape(self.markers["end"])}',
            re.DOTALL,
        )
        return pattern.sub("", content).strip()

    def backup_file(self, file_path):
        """Create a backup of the file"""
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")
        if file_path.exists():
            shutil.copy2(file_path, backup_path)
            print(f"Backup created: {backup_path}")

    def update_shell_config(self, config_path):
        """Update a shell configuration file"""
        if not config_path.exists():
            print(f"Creating new file: {config_path}")
            config_path.touch()

        # Read current content
        current_content = config_path.read_text().strip()

        # Backup the file
        self.backup_file(config_path)

        # Remove existing section if it exists
        if self.find_existing_section(current_content):
            print(f"Removing existing local-helpers section from {config_path}")
            new_content = self.remove_existing_section(current_content)
        else:
            new_content = current_content

        # Add new section
        alias_content = self.generate_alias_content()
        if new_content:
            new_content = f"{new_content}\n\n{alias_content}"
        else:
            new_content = alias_content

        # Write updated content
        config_path.write_text(new_content)
        print(f"Updated {config_path} with new aliases")

    def verify_scripts_exist(self):
        """Verify that all scripts referenced in aliases exist"""
        missing_scripts = []
        for alias_name, command in self.aliases.items():
            # Only check for script files (ending with .sh or .py)
            if command.endswith(".sh") or command.endswith(".py"):
                script_path = self.script_dir / command
                if not script_path.exists():
                    missing_scripts.append(command)

        if missing_scripts:
            print(
                "Warning: The following scripts are referenced in aliases but were not found:"
            )
            for script in missing_scripts:
                print(f"  - {script}")
            print("Aliases for these scripts will be created but may not work.")

        return len(missing_scripts) == 0

    def display_aliases(self):
        """Display the aliases that will be created"""
        if not self.aliases:
            print("No aliases found in alias.txt")
            return

        print("Aliases to be created:")
        for alias_name, command in self.aliases.items():
            if "(){" in command:
                print(f"  {alias_name}() (function)")
            elif command.endswith(".sh") or command.endswith(".py"):
                script_path = self.get_script_absolute_path(command)
                if command.endswith(".sh"):
                    print(f"  {alias_name} -> {script_path}")
                elif command.endswith(".py"):
                    print(f"  {alias_name} -> python3 {script_path}")
            else:
                print(f"  {alias_name} -> {command}")

    def run(self):
        """Main method to run the setup"""
        print("Local Helpers Setup")
        print("=" * 50)

        # Check if we have any aliases
        if not self.aliases:
            print(
                "No aliases found in alias.txt. Please create an alias.txt file with your aliases."
            )
            return

        # Display what will be created
        self.display_aliases()
        print()

        # Verify scripts exist
        all_scripts_exist = self.verify_scripts_exist()
        if not all_scripts_exist:
            print()

        # Update shell configurations
        print("Updating shell configurations...")

        if self.bashrc_path.exists() or input("Create .bashrc? (y/n): ").lower() == "y":
            self.update_shell_config(self.bashrc_path)
            print(f"Bash configuration updated")
        else:
            print("Skipping .bashrc")

        if self.zshrc_path.exists() or input("Create .zshrc? (y/n): ").lower() == "y":
            self.update_shell_config(self.zshrc_path)
            print(f"Zsh configuration updated")
        else:
            print("Skipping .zshrc")

        print("\nSetup complete!")
        print("\nTo use the new aliases, run:")
        print("  source ~/.bashrc  # for bash")
        print("  source ~/.zshrc   # for zsh")
        print("\nOr restart your terminal.")


def main():
    manager = ShellConfigManager()
    manager.run()


if __name__ == "__main__":
    main()
