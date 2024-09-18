import os
import re
import argparse
import tiktoken

# Constants
CODE_FILES = ['.php', '.json', '.env', '.blade.php', '.js', '.css', '.md', '.html']

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
        # '.file_extension': ('single_line_comment', 'multi_line_comment_start', 'multi_line_comment_end')
        '.php': ('//', '/*', '*/'),
        '.js': ('//', '/*', '*/'),
        '.css': (None, '/*', '*/'),
        '.html': (None, '<!--', '-->'),
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
            if multi_start and multi_end:
                content = re.sub(re.escape(multi_start) + r'.*?' + re.escape(multi_end), '', content, flags=re.DOTALL)
            # Remove single-line comments if defined
            if single:
                content = re.sub(re.escape(single) + r'.*$', '', content, flags=re.MULTILINE)

    return content

def clean_content(content):
    """Clean content by removing trailing spaces and empty lines."""
    lines = content.splitlines()
    trimmed_lines = [line.rstrip() for line in lines if line.strip()]
    return "\n".join(trimmed_lines)

def concat_files(filenames, output_base, max_tokens, keep_comments, line_numbers, show_full_path, show_path, encoding):
    """Concatenate content from given filenames and handle comments."""
    concatenated_content = ""
    current_part = 1
    current_tokens = 0

    print("TOKENS | FILENAME")

    for filename, original_filename in filenames:
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
                displayed_filename = original_filename if show_path else filename if show_full_path else os.path.basename(filename)
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

def gather_files_from_input(input_path, debug):
    """Gather files from input, taking into account the TARGET prefix."""
    source_files = []
    target_prefix = None

    # If input is a directory, gather files directly
    if os.path.isdir(input_path):
        return [(f, f) for f in gather_files(input_path)], target_prefix

    # If input is a file list, process the file
    if os.path.isfile(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        # Check if the first line is a TARGET prefix
        if lines[0].startswith("TARGET:"):
            target_prefix = lines[0].replace("TARGET:", "").strip()
            lines = lines[1:]  # Skip the TARGET line

        for path in lines:
            if not path.startswith("#"):  # Ignore commented-out lines
                original_path = path  # Store original non-prefixed path
                if target_prefix:
                    path = os.path.join(target_prefix, path.lstrip("/"))
                source_files.append((path, original_path))

        if debug:
            print(f"Debug: Target prefix is '{target_prefix}'")

    return source_files, target_prefix

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process and concatenate files from given paths or directories.')
    parser.add_argument('input_path', type=str, help='Directory path or file containing list of paths to search for files.')
    parser.add_argument('-o', '--output', required=False, type=str, default="prompt", help='Output file prefix. Defaults to "prompt.txt" if not specified.')
    parser.add_argument('--line-numbers', action='store_true', help='Prefix lines with their line numbers.')
    parser.add_argument('--keep-comments', action='store_true', help='Retain comments in files.')
    parser.add_argument('--show-full-path', action='store_true', help='Display the full path of files.')
    parser.add_argument('--show-path', action='store_true', help='Display the non-prefixed path of files.')
    parser.add_argument('--max-tokens', required=False, type=int, help='Max tokens per output file part.')
    parser.add_argument('--concise', action='store_true', help='Remove non-crucial lines like imports and package names.')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    # Gather files and handle the TARGET prefix if present
    source_files, target_prefix = gather_files_from_input(args.input_path, args.debug)

    try:
        encoding = tiktoken.encoding_for_model('gpt-4')
    except Exception:
        encoding = None  # Consider providing a fallback or default handling if tiktoken fails

    output_base = args.output if args.output else os.path.splitext(args.input_path)[0]  # Use input_path's base if no output is provided
    final_output = concat_files(source_files, output_base, args.max_tokens, args.keep_comments, args.line_numbers, args.show_full_path, args.show_path, encoding)
