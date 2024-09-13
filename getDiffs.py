import subprocess
import os
import sys
import shutil

def get_git_status(repo_dir):
    """Get the summary of changes."""
    os.chdir(repo_dir)
    result = subprocess.run(['git', 'diff', '--name-status'], stdout=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("Failed to get the summary of changes.")
        return None
    return result.stdout

def create_summary_file(summary, output_dir):
    """Create a summary file with the output of git diff --name-status."""
    summary_file_path = os.path.join(output_dir, "summary_of_changes.txt")
    with open(summary_file_path, 'w') as f:
        f.write(summary)
    print(f"Summary of changes written to {summary_file_path}")

def create_diff_files(repo_dir, output_dir, summary):
    """Create diff files for each changed file."""
    lines = summary.strip().split('\n')
    for line in lines:
        status, file_path = line.split(maxsplit=1)
        if status == 'D':  # Skip deleted files
            continue
        # Replace slashes with underscores to avoid name conflicts and adhere to file naming conventions
        filename = file_path.replace('/', '_').replace('\\', '_') + '.diff'
        diff_result = subprocess.run(['git', 'diff', file_path], stdout=subprocess.PIPE, text=True)
        output_file_path = os.path.join(output_dir, filename)
        with open(output_file_path, 'w') as f:
            f.write(diff_result.stdout)
        print(f"Diff for {file_path} written to {output_file_path}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_repo>")
        sys.exit(1)

    repo_dir = sys.argv[1]
    output_dir = os.path.join(os.path.dirname(__file__), "diff_output")

    if os.path.exists(output_dir):
        user_input = input("Output directory exists. Overwrite? (yes/no): ")
        if user_input.lower() != 'yes':
            print("Operation aborted by user.")
            sys.exit(0)
        shutil.rmtree(output_dir)
        os.makedirs(output_dir)
    else:
        os.makedirs(output_dir)

    summary = get_git_status(repo_dir)
    if summary:
        create_summary_file(summary, output_dir)
        create_diff_files(repo_dir, output_dir, summary)

if __name__ == '__main__':
    main()
