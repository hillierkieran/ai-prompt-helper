import os
import sys
import argparse
try:
    import tiktoken  # type: ignore
except ImportError:
    print("Error: Failed to import 'tiktoken'. Please make sure it is installed.")
    sys.exit(1)

# Hardcoded token limits for each model
MODEL_LIMITS = {
    'gpt-4': 8192,
    'gpt-4o': 8192,
    'gpt-4o-mini': 8192,
}

def gather_files(directory_path):
    """Gather all files recursively from the given directory."""
    all_files = []
    for root, _, filenames in os.walk(directory_path):
        for filename in filenames:
            all_files.append(os.path.join(root, filename))
    return all_files

def count_tokens_from_file(file_path, encoding):
    """Count the number of tokens in the provided file using specified encoding."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tokens = encoding.encode(content)
        return len(tokens)
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Token Counter for Files or Directories')
    parser.add_argument('path', type=str, help='Path to file or directory to count tokens')
    parser.add_argument('--model', default='gpt-4', choices=MODEL_LIMITS.keys(), help='Model to use for token counting')

    args = parser.parse_args()

    # Set encoding based on model
    encoding = tiktoken.encoding_for_model(args.model)

    if os.path.isdir(args.path):
        # If it's a directory, gather all files and count tokens for each
        files = gather_files(args.path)
    else:
        # If it's a single file, just use that file
        files = [args.path]


    # Print header
    print("TOKENS | FILENAME")

    total_tokens = 0
    # Iterate through files and count tokens
    for file_path in files:
        token_count = count_tokens_from_file(file_path, encoding)
        if token_count is not None:
            total_tokens += token_count
            space_padding = 6 - len(str(token_count))
            print(f"{' ' * space_padding}{token_count} | {file_path}")


    print("_______|____________________")

    # Print total token count
    space_padding = 6 - len(str(total_tokens))
    print(f"{' ' * space_padding}{total_tokens} | Total Tokens")

    # Print the model's max input size
    max_length = MODEL_LIMITS[args.model]
    space_padding = 6 - len(str(max_length))
    print(f"{' ' * space_padding}{max_length} | {args.model} max input size")

if __name__ == "__main__":
    main()
