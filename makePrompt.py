import os
import re
import argparse
import tiktoken

# Constants
CODE_FILES = ['.php', '.json', '.env', '.blade.php', '.js', '.css', '.md']

# Utility Functions
def gather_files(directory_path):
    """Gather all files recursively from the given directory."""
    return [os.path.join(root, filename) for root, _, filenames in os.walk(directory_path) for filename in filenames]

def count_tokens(content, encoding):
    """Count tokens in a given content string."""
    try:
        return len(encoding.encode(content))
    except Exception:
        return 0

def prefix_with_line_numbers(content, line_numbers):
    """Prefix each line of content with its line number if requested."""
    if line_numbers:
        return "\n".join(f"{i + 1}|{line}" for i, line in enumerate(content.splitlines()))
    return content

def remove_non_crucial_lines(content, extension, concise):
    """Remove non-crucial lines like imports, package declarations if requested."""
    if not concise:
        return content

    lines = content.splitlines()
    prefixed_content = all('|' in line for line in lines)

    def get_content_of_line(line):
        """Retrieve the actual content of the line, excluding any line number prefix."""
        return line.split('|', 1)[1].strip() if prefixed_content else line.strip()

    import_startswith = {
        '.php': 'use ',
        '.js': 'import ',
        '.css': '@import ',
    }

    if extension in import_startswith:
        lines = [line for line in lines if not get_content_of_line(line).startswith(import_startswith[extension])]

    return '\n'.join(lines)

def detect_full_extension(filename):
    """Detect the full extension"""
    # Handle .env files explicitly
    if os.path.basename(filename) == '.env':
        return '.env'

    # Handle compound extensions like .blade.php.
    _, ext = os.path.splitext(filename)
    if ext == '.php' and filename.endswith('.blade.php'):
        return '.blade.php'
    return ext

def remove_comments(content, extension, keep_comments):
    """Remove comments from content if not keeping them."""
    if keep_comments:
        return content

    # Detect full file extension, including compound extensions like .blade.php
    full_extension = detect_full_extension(extension)

    # Debugging: Output the detected extension
    if args.debug:
        print(f"Debug: Detected file extension as '{full_extension}' for file '{extension}'")

    comment_rules = {
        '.php': ('//', '/*', '*/'),
        '.js': ('//', '/*', '*/'),
        '.css': ('/*', '*/'),
        '.blade.php': ('{{--', '--}}', '<!--', '-->'),
        '.env': ('#', None, None),
    }

    if full_extension in comment_rules:
        if full_extension == '.blade.php':
            # Remove Blade-style comments {{-- ... --}}
            content = re.sub(r'\{\{--.*?--\}\}', '', content, flags=re.DOTALL)
            # Remove HTML-style comments <!-- ... -->
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        else:
            single, multi_start, multi_end = comment_rules[full_extension]
            # Remove multiline comments
            if (multi_start and multi_end):
                content = re.sub(re.escape(multi_start) + r'.*?' + re.escape(multi_end), '', content, flags=re.DOTALL)
            # Remove single-line comments
            content = re.sub(re.escape(single) + r'.*$', '', content, flags=re.MULTILINE)

    return content

def clean_content(content):
    """Clean content by removing trailing spaces and empty lines."""
    lines = content.splitlines()
    trimmed_lines = [line.rstrip() for line in lines if line.strip()]
    return "\n".join(trimmed_lines)

def concat_files(filenames, output_base, max_tokens, keep_comments, line_numbers, show_full_path, encoding):
    """Concatenate content from given filenames and handle comments."""
    concatenated_content = ""
    current_part = 1
    current_tokens = 0

    print("TOKENS | FILENAME")

    for filename in filenames:
        code_file = filename.endswith(tuple(CODE_FILES))
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
                if not content.strip():
                    print(f"       | {filename}")
                    continue

                # Full extension for proper processing
                extension = filename

                # Debugging: Output the filename being processed
                if args.debug:
                    print(f"Debug: Processing file '{filename}'")

                content = prefix_with_line_numbers(content, line_numbers)
                content = remove_comments(content, extension, keep_comments)
                content = remove_non_crucial_lines(content, extension, args.concise)
                content = clean_content(content)

                file_tokens = count_tokens(content, encoding)
                space_padding = 6 - len(str(file_tokens))
                print(f"{' ' * space_padding}{file_tokens} | {filename}")

                current_tokens += file_tokens
                separator = "\n\n\n" if concatenated_content else ""
                displayed_filename = filename if show_full_path else os.path.basename(filename)
                concatenated_content += f"{separator}{displayed_filename}:\n"
                concatenated_content += "```\n" if code_file else "\"\n"
                concatenated_content += f"{content}\n"
                concatenated_content += "```\n" if code_file else "\"\n"

                if max_tokens and current_tokens > max_tokens:
                    output_path = f"{output_base}_part{current_part}.txt"
                    with open(output_path, 'w', encoding='utf-8') as output_file:
                        output_file.write(concatenated_content)

                    print(f"{output_path} contains {current_tokens} tokens.")
                    current_part += 1
                    concatenated_content = ""
                    current_tokens = 0

        except Exception as e:
            print(f"Error processing file {filename}: {e}")

    if concatenated_content:
        output_filename = f"{output_base}_part{current_part}.txt" if current_part > 1 else f"{output_base}.txt"
        with open(output_filename, 'w', encoding='utf-8') as output_file:
            output_file.write(concatenated_content)

        # Print total token count
        print("_______|____________________")
        space_padding = 6 - len(str(current_tokens))
        print(f"{' ' * space_padding}{current_tokens} | Output file `{output_filename}`")
        return output_filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process and concatenate files from given paths or directories.')
    parser.add_argument('input_path', type=str, help='Directory path or file containing list of paths to search for files.')
    parser.add_argument('-o', '--output', required=False, type=str, default="prompt", help='Output file prefix. Defaults to "prompt.txt" if not specified.')
    parser.add_argument('--line-numbers', action='store_true', help='Prefix lines with their line numbers.')
    parser.add_argument('--keep-comments', action='store_true', help='Retain comments in files.')
    parser.add_argument('--show-full-path', action='store_true', help='Display the full path of files.')
    parser.add_argument('--max-tokens', required=False, type=int, help='Max tokens per output file part.')
    parser.add_argument('--concise', action='store_true', help='Remove non-crucial lines like imports and package names.')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    # Determine if the input is a directory or a file list
    if os.path.isdir(args.input_path):
        source_files = gather_files(args.input_path)
    elif os.path.isfile(args.input_path):
        with open(args.input_path, 'r', encoding='utf-8') as f:
            paths = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        source_files = []
        for path in paths:
            source_files.extend(gather_files(path) if os.path.isdir(path) else [path])
    else:
        print("The specified input path does not exist.")
        sys.exit(1)

    try:
        encoding = tiktoken.encoding_for_model('gpt-4')
    except Exception:
        encoding = None  # Consider providing a fallback or default handling if tiktoken fails

    output_base = args.output if args.output else os.path.splitext(args.input_path)[0]  # Use input_path's base if no output is provided
    final_output = concat_files(source_files, output_base, args.max_tokens, args.keep_comments, args.line_numbers, args.show_full_path, encoding)
