"""
This script generates a directory tree structure for a given directory and writes it to a file.
"""

import os
import sys
try:
    import pathspec # type: ignore
except ImportError:
    print("Error: Failed to import 'pathspec'. Please make sure it is installed.")
    sys.exit(1)

"""
Recursively generates a directory tree structure.

Args:
    directory_path (str): The path of the directory to generate the tree for.
    indent (str): The indentation string for each level of the tree.
    spec (pathspec.PathSpec): The PathSpec object for `.gitignore` rules.

Returns:
    str: The generated directory tree structure.
"""
def generate_directory_tree(directory_path, indent="", spec=None):
    tree = ""
    items = os.listdir(directory_path)  # Get list of all items in the directory
    items.sort()  # Sort the items for consistent output

    # Iterate over each item in the directory
    for index, item in enumerate(items):
        item_path = os.path.join(directory_path, item)
        # Check if the item should be ignored based on .gitignore rules or if it's the .git directory
        if item == '.git' or (spec and spec.match_file(os.path.relpath(item_path, start=directory_path))):
            continue
        # Check if the item is the last one in the directory
        is_last = index == len(items) - 1

        # If the item is a directory...
        if os.path.isdir(item_path):
            # Add it to the tree with appropriate indentation
            tree += f"{indent}{'└── ' if is_last else '├── '}{item}/\n"
            # Recursively generate the tree structure for the subdirectory
            tree += generate_directory_tree(item_path, indent + ("    " if is_last else "│   "), spec)
        # Else, if the item is a file...
        else:
            # Add it to the tree with appropriate indentation
            tree += f"{indent}{'└── ' if is_last else '├── '}{item}\n"

    # Return the generated tree structure
    return tree

"""
Reads the .gitignore file and returns a PathSpec object.

Args:
    directory_path (str): The path of the directory to look for .gitignore.

Returns:
    pathspec.PathSpec: The PathSpec object for .gitignore rules, or None if no .gitignore file is found.
"""
def load_gitignore(directory_path):
    gitignore_path = os.path.join(directory_path, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as gitignore_file:
            return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, gitignore_file)
    return None

"""
The main entry point of the program.
"""
if __name__ == "__main__":
    # Check if the correct number of command-line arguments has been provided
    if len(sys.argv) != 3:
        print("Usage: python generate_directory_tree.py <input_directory> <output_file>")
        sys.exit(1)

    input_directory = sys.argv[1]
    output_file = sys.argv[2]

    # Check if the input directory exists
    if not os.path.exists(input_directory):
        print(f"Error: Input directory '{input_directory}' does not exist.")
        sys.exit(1)

    # Load .gitignore rules if present
    spec = load_gitignore(input_directory)

    # Generate directory tree
    directory_tree = f"{input_directory}/\n{generate_directory_tree(input_directory, spec=spec)}"

    # Write the generated directory tree to the output file with UTF-8 encoding
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(directory_tree)

    print(f"Tree written to {output_file}")