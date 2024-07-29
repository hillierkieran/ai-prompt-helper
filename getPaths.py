import os
import argparse

def list_all_files_in_directory(directory, file_types=None):
    for root, _, files in os.walk(directory):
        for file in files:
            if file_types is None or any(file.endswith(file_type) for file_type in file_types):
                yield os.path.join(root, file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=str, help="The directory to search")
    parser.add_argument("-o", "--output", type=str, default="paths.txt", help="The output file to write the paths to")
    parser.add_argument("-t", "--filetypes", nargs="+", help="List of file types to include")

    args = parser.parse_args()

    with open(args.output, 'w') as f:
        for file_path in list_all_files_in_directory(args.directory, args.filetypes):
            f.write(file_path + '\n')

    print(f"Paths written to {args.output}.")