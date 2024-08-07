import os
import re
import argparse
import tiktoken

# Constants
CODE_FILES = ['.php', '.json', '.env', '.blade.php', '.js', '.css']

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

def prefix_with_line_numbers(content):
    """Prefix each line of content with its line number."""
    return "\n".join(f"{i + 1}|{line}" for i, line in enumerate(content.splitlines()))

# Content Processing Functions
def remove_non_crucial_lines(content, extension):
    """Remove non-crucial lines like imports, package declarations."""
    lines = content.splitlines()

    # Determine if every line has a prefix (and hence is a prefixed content)
    prefixed_content = all('|' in line for line in lines)

    def get_content_of_line(line):
        """Retrieve the actual content of the line, excluding any line number prefix."""
        return line.split('|', 1)[1].strip() if prefixed_content else line.strip()

    # Removing package declarations and imports for common languages
    import_startswith = {
        '.php': 'use ',
        '.js': 'import ',
        '.css': '@import ',
    }

    if extension in import_startswith:
        lines = [line for line in lines if not get_content_of_line(line).startswith(import_startswith[extension])]

    return '\n'.join(lines)

def remove_comments(content, single, multi_start=None, multi_end=None):
    """Remove comments from content."""
    if multi_start and multi_end:
        content = re.sub(re.escape(multi_start) + r'.*?' + re.escape(multi_end), '', content, flags=re.DOTALL)
    content = re.sub(re.escape(single) + r'.*$', '', content, flags=re.MULTILINE)
    return content

def clean_content(content):
    lines = content.splitlines()
    prefixed_content = all('|' in line for line in lines)

    trimmed_lines = []
    for line in lines:
        trimmed_line = line.rstrip()
        if prefixed_content:
            if trimmed_line.split('|', 1)[1].strip():
                trimmed_lines.append(trimmed_line)
        else:
            if trimmed_line.strip():
                trimmed_lines.append(trimmed_line)

    return "\n".join(trimmed_lines)

# Concatenation Function
def concat_files(filenames, output_base, max_tokens=None, keep_comments=False):
    """Concatenate content from given filenames and handle comments."""
    concatenated_content = ""
    current_part = 1
    current_tokens = 0

    for filename in filenames:
        code_file = filename.endswith(tuple(CODE_FILES))
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
                if not content.strip():
                    print(f"Skipped empty file: {filename}")
                    continue

                if code_file and args.line_numbers:
                    content = prefix_with_line_numbers(content)

                if not keep_comments:
                    comment_rules = {
                        '.php': ('//', '/*', '*/'),
                        '.js': ('//', '/*', '*/'),
                        '.css': ('/*', '*/'),
                    }
                    for exts, rules in comment_rules.items():
                        if filename.endswith(exts):
                            content = remove_comments(content, *rules)
                            break

                if args.concise:
                    content = remove_non_crucial_lines(content, os.path.splitext(filename)[1])

                content = clean_content(content)

                current_tokens += count_tokens(content, encoding)
                separator = "\n\n\n" if concatenated_content else ""
                displayed_filename = filename if args.show_full_path else os.path.basename(filename)
                concatenated_content += f"{separator}{displayed_filename}:\n"
                concatenated_content += "```\n" if code_file else "\"\n"
                concatenated_content += f"{content}\n"
                concatenated_content += "```\n" if code_file else "\"\n"

                if max_tokens and current_tokens > max_tokens:
                    output_path = f"{output_base}_part{current_part}"
                    with open(output_path, 'w', encoding='utf-8') as output_file:
                        output_file.write(concatenated_content)

                    print(f"{output_path} contains {current_tokens} tokens.")
                    current_part += 1
                    concatenated_content = ""
                    current_tokens = 0

        except Exception as e:
            print(f"Error processing file {filename}: {e}")

    output_filename = f"{output_base}" if current_part == 1 else f"{output_base}_part{current_part}"
    with open(output_filename, 'w', encoding='utf-8') as output_file:
        output_file.write(concatenated_content)

    print(f"{output_filename} contains {current_tokens} tokens.")
    return output_filename  # Return the final path for printing purposes.

# Main Script Execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process and concatenate files.')
    parser.add_argument('input_file', type=str, help='File containing list of paths or directory to search for files.')
    parser.add_argument('-o', '--output', required=False, type=str, default="prompt.txt", help='Output file prefix. If not provided, it will overwrite the input file.')
    parser.add_argument('--line-numbers', action='store_true', help='Prefix lines with their line numbers.')
    parser.add_argument('--keep-comments', action='store_true', help='Retain comments in files.')
    parser.add_argument('--show-full-path', action='store_true', help='Display the full path of files.')
    parser.add_argument('--max-tokens', required=False, type=int, help='Max tokens per output file.')
    parser.add_argument('--concise', action='store_true', help='Remove non-crucial lines like imports and package names.')

    args = parser.parse_args()

    source_files = []
    with open(args.input_file, 'r', encoding='utf-8') as f:
        paths = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    for path in paths:
        source_files.extend(gather_files(path) if os.path.isdir(path) else [path])

    try:
        encoding = tiktoken.encoding_for_model('gpt-4')
    except Exception:
        encoding = None

    output_base = args.output if args.output else os.path.splitext(args.input_file)[0]  # Use input_file's base if no output is provided
    final_output = concat_files(source_files, output_base, args.max_tokens, args.keep_comments)
