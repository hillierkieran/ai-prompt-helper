import os
import re
import argparse
import tiktoken

# Constants
CODE_FILES = [
    '.blade.php', '.php',
    '.css',
    '.env',
    '.html',
    '.js', '.svelte',
    '.json',
    '.md',
    '.sql',
    '.cs',
    '.diff',
    '.csv',
    '.tree',
]

# Mapping of file extensions to language names for markdown code blocks
LANGUAGE_MAP = {
    '.blade.php': 'php',
    '.php': 'php',
    '.css': 'css',
    '.env': 'plaintext',
    '.html': 'html',
    '.js': 'javascript',
    '.svelte': 'javascript',
    '.json': 'json',
    '.md': 'markdown',
    '.sql': 'sql',
    '.cs': 'csharp',
    '.diff': 'diff',
    '.csv': '',
}

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
        '.svelte': 'import ',
        '.css': '@import ',
        '.sql': 'USE ',
        '.sql': 'using ',
        '.cs': 'using ',
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
        '.blade.php': ('{{--', '--}}', '<!--', '-->'),
        '.php': ('//', '/*', '*/'),
        '.js': ('//', '/*', '*/'),
        '.svelte': ('//', '/*', '*/'),
        '.json': ('//', '/*', '*/'),
        '.css': (None, '/*', '*/'),
        '.html': (None, '<!--', '-->'),
        '.env': ('#', None, None),
        '.sql': ('--', '/*', '*/'),
        '.cs': ('//', '/*', '*/'),
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
                # Remove lines that only contain a multiline comment
                content = re.sub(r'^[ \t]*' + re.escape(multi_start) + r'.*?' + re.escape(multi_end) + r'[ \t]*$\n?', '', content, flags=re.MULTILINE | re.DOTALL)
                # Remove in-line multiline comments
                content = re.sub(re.escape(multi_start) + r'.*?' + re.escape(multi_end), '', content, flags=re.DOTALL)

            # Remove full-line single comments
            if single:
                # Remove lines that only contain a single-line comment
                content = re.sub(r'^[ \t]*' + re.escape(single) + r'.*[ \t]*$\n?', '', content, flags=re.MULTILINE)
                # Remove in-line single-line comments
                content = re.sub(re.escape(single) + r'.*$', '', content, flags=re.MULTILINE)

    return content

def clean_content(content):
    """Clean content by removing trailing spaces."""
    lines = content.splitlines()
    trimmed_lines = [line.rstrip() for line in lines]
    return "\n".join(trimmed_lines)

def read_file_with_fallback_encoding(file_path):
    """Attempt to read a file with UTF-8, and fall back to other encodings if necessary."""
    encodings = ['utf-8', 'utf-16', 'latin-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"Unable to decode file {file_path} with any of the supported encodings: {encodings}")

def concat_files(filenames, output_base, max_tokens, keep_comments, line_numbers, show_full_path, show_path, encoding):
    """Concatenate content from given filenames and handle comments."""
    concatenated_content = ""
    current_part = 1
    current_tokens = 0

    print("TOKENS | FILENAME")

    for filename, original_filename in filenames:
        code_file = filename.endswith(tuple(CODE_FILES))
        try:
            # Use the fallback encoding function to read the file
            content = read_file_with_fallback_encoding(filename)
            if not content.strip():
                print(f"       | {filename}")
                continue

            # Extract the file extension
            extension = os.path.splitext(filename)[1]  # Keeps the leading dot, e.g., ".cs"

            # Check if the extension is in the LANGUAGE_MAP, otherwise default to "plaintext"
            language = LANGUAGE_MAP.get(extension, "plaintext")

            # Debugging: Output the filename being processed
            if args.debug:
                print(f"Debug: Processing file '{filename}'")

            content = prefix_with_line_numbers(content, line_numbers)
            content = remove_comments(content, filename, keep_comments)
            content = remove_non_crucial_lines(content, filename, args.concise)
            content = clean_content(content)

            file_tokens = count_tokens(content, encoding)
            space_padding = 6 - len(str(file_tokens))
            print(f"{' ' * space_padding}{file_tokens} | {filename}")

            current_tokens += file_tokens
            separator = "\n\n\n--------------------------------------------------------------------------------\n\n\n\n" if concatenated_content else ""
            displayed_filename = original_filename if show_path else filename if show_full_path else os.path.basename(filename)
            concatenated_content += f"{separator}{displayed_filename}:\n"
            concatenated_content += f"```{language}\n" if code_file else "\"\"\"\n"
            concatenated_content += f"{content.lstrip("\ufeff")}\n"
            concatenated_content += "```\n" if code_file else "\"\"\"\n"

            if max_tokens and current_tokens > max_tokens:
                output_path = f"{output_base}_part{current_part}.md"
                with open(output_path, 'w', encoding='utf-8-sig') as output_file:
                    output_file.write(concatenated_content)

                print(f"{output_path} contains {current_tokens} tokens.")
                current_part += 1
                concatenated_content = ""
                current_tokens = 0

        except Exception as e:
            print(f"Error processing file {filename}: {e}")

    if concatenated_content:
        output_filename = f"{output_base}_part{current_part}.md" if current_part > 1 else f"{output_base}.md"
        with open(output_filename, 'w', encoding='utf-8') as output_file:
            output_file.write(concatenated_content)

        # Print total token count
        print("_______|____________________")
        space_padding = 6 - len(str(current_tokens))
        print(f"{' ' * space_padding}{current_tokens} | Output file `{output_filename}`")
        return output_filename

def gather_files_from_input(input_path, debug):
    """Gather files from input, handling multiple TARGET prefixes."""
    source_files = []  # List to store tuples of (full_path, original_path)
    current_target = None  # Variable to store the current TARGET prefix

    # If the input is a directory, gather all files directly
    if os.path.isdir(input_path):
        return [(f, f) for f in gather_files(input_path)], None

    # If the input is a file, process it line by line
    if os.path.isfile(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()  # Remove leading/trailing whitespace
                if not line:  # Skip empty lines
                    continue

                # Check if the line starts with "TARGET:"
                if line.startswith("TARGET:"):
                    # Update the current_target to the new TARGET prefix
                    current_target = line.replace("TARGET:", "").strip()
                    if debug:
                        print(f"Debug: New target prefix set to '{current_target}'")

                # If the line is not a comment (starts with "#"), process it as a file path
                elif not line.startswith("#"):
                    original_path = line  # Store the original non-prefixed path
                    # Construct the full path by joining the current_target with the file path
                    full_path = os.path.join(current_target, line.lstrip("/")) if current_target else line
                    # Add the (full_path, original_path) tuple to the source_files list
                    source_files.append((full_path, original_path))

    # Return the list of files and the last TARGET prefix (for debugging purposes)
    return source_files, current_target

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process and concatenate files from given paths or directories.')
    parser.add_argument('input_path', type=str, help='Directory path or file containing list of paths to search for files.')
    parser.add_argument('-o', '--output', required=False, type=str, default="prompt", help='Output file prefix. Defaults to "prompt.md" if not specified.')
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