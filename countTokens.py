import sys
try:
    import tiktoken # type: ignore
except ImportError:
    print("Error: Failed to import 'tiktoken'. Please make sure it is installed.")
    sys.exit(1)


def count_tokens_from_file(file_path, encoding):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    tokens = encoding.encode(content)
    return len(tokens)


def main():
    # Check if file path is provided
    if len(sys.argv) < 2:
        print("Usage: python countTokens.py <input_file> [model]")
        print("Model options: gpt-3.5, gpt-4, gpt-4o, gpt-4o-mini")
        print("Default model is 'gpt-4'.")
        return

    file_path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else 'gpt-4'

    # Set encoding and context length based on model
    if model == 'gpt-3.5':
        encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')
        context_length = 16000
    elif model in ['gpt-4', 'gpt-4o', 'gpt-4o-mini']:
        encoding = tiktoken.encoding_for_model('gpt-4')
        context_length = 128000
    else:
        print("Unsupported model.")
        return

    # Get the token count
    token_count = count_tokens_from_file(file_path, encoding)

    # Check if the token count fits within the context window
    if token_count > context_length:
        print(f"TOO BIG: '{file_path}' contains {token_count} tokens, exceeding {model}'s {context_length} token context window.")
    else:
        print(f"SUCCESS: '{file_path}' contains {token_count} tokens, fitting within {model}'s {context_length} token context window.")

if __name__ == "__main__":
    main()
