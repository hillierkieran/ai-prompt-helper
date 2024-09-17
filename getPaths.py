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
    for root, dirs, files in os.walk(directory):
        # Ignore the .git directory
        if '.git' in dirs:
            dirs.remove('.git')

        for file in files:
            # Get relative file path and normalize to forward slashes
            file_path = os.path.relpath(os.path.join(root, file), directory).replace('\\', '/')

            # Check if the file is ignored by .gitignore
            if gitignore_spec and gitignore_spec.match_file(file_path):
                continue

            # Check file types
            if file_types is None or any(file.endswith(file_type) for file_type in file_types):
                yield file_path

def get_output_filename(directory, output=None):
    if output is None:
        # Create the paths directory if it doesn't exist
        os.makedirs('./paths', exist_ok=True)

        # Get the last part of the target directory and use it to name the output file
        dir_name = os.path.basename(os.path.normpath(directory))
        output = f"./paths/{dir_name}.txt"

    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=str, help="The directory to search")
    parser.add_argument("-o", "--output", type=str, help="The output file to write the paths to")
    parser.add_argument("-t", "--filetypes", nargs="+", help="List of file types to include")

    args = parser.parse_args()

    # Load .gitignore if present
    gitignore_spec = load_gitignore(args.directory)

    # Determine the output filename
    output_file = get_output_filename(args.directory, args.output)

    # Get absolute path of the target directory
    abs_directory = os.path.abspath(args.directory)

    # Write the paths to the output file, prefixed with "#   "
    with open(output_file, 'w') as f:
        # Write the absolute path to the directory with 'TARGET:' prefix
        f.write(f"TARGET: {abs_directory}\n\n")  # Absolute path followed by a blank line

        # Write all file paths, stripped of the preceding relative path
        for file_path in list_all_files_in_directory(args.directory, args.filetypes, gitignore_spec):
            f.write(f"#   {file_path}\n")

    print(f"Paths written to {output_file}.")
