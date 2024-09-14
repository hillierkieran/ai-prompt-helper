import os
import argparse
from pathspec import PathSpec

def load_gitignore(directory):
    gitignore_path = os.path.join(directory, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            return PathSpec.from_lines('gitwildmatch', f)
    return None

def list_all_files_in_directory(directory, file_types=None, gitignore_spec=None):
    for root, _, files in os.walk(directory):
        for file in files:
            # Get relative file path and normalize to forward slashes
            file_path = os.path.relpath(os.path.join(root, file), directory).replace('\\', '/')

            # Check if the file is ignored by .gitignore
            if gitignore_spec and gitignore_spec.match_file(file_path):
                continue

            # Check file types
            if file_types is None or any(file.endswith(file_type) for file_type in file_types):
                yield os.path.join(root, file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=str, help="The directory to search")
    parser.add_argument("-o", "--output", type=str, default="paths.txt", help="The output file to write the paths to")
    parser.add_argument("-t", "--filetypes", nargs="+", help="List of file types to include")

    args = parser.parse_args()

    # Load .gitignore if present
    gitignore_spec = load_gitignore(args.directory)

    with open(args.output, 'w') as f:
        for file_path in list_all_files_in_directory(args.directory, args.filetypes, gitignore_spec):
            f.write(file_path + '\n')

    print(f"Paths written to {args.output}.")
