import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://git.oraclecms.com:3000"
REPO_OWNER = "Kieran"
REPO_NAME = "LoneWorkerRebuild"
OUTPUT_FILE = "./tmp/open_issues.txt"
TOKEN = "ad7bbb0e7563c44e5953563dce11bfba1cce7873"

def get_issue_numbers(base_url, owner, repo):
    """Retrieve all open issue numbers from the repository using the Gitea API"""
    issue_numbers = []
    page = 1
    headers = {"Authorization": f"token {TOKEN}"}

    url = f"{base_url}/api/v1/repos/{owner}/{repo}/issues"
    print(f"Fetching issues from: {url}")

    while True:
        params = {"state": "open", "page": page, "limit": 50}  # Adjust limit as needed
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Failed to fetch issues. HTTP Status: {response.status_code}")
            print(f"Response: {response.text}")
            break

        issues = response.json()
        if not issues:
            break

        for issue in issues:
            issue_numbers.append(issue["number"])

        page += 1

    return issue_numbers

def parse_issue_page(url):
    """Fetch issue details using the Gitea API and return structured data"""
    headers = {"Authorization": f"token {TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch issue page. HTTP Status: {response.status_code}")
        return None

    issue = response.json()

    # Extract basic info
    title = issue.get("title", "Untitled")
    author = issue.get("user", {}).get("login", "Unknown")
    date = issue.get("created_at", "Unknown")
    body = issue.get("body", "")
    comments = []

    # Fetch comments if available and comments_url is valid
    comments_url = issue.get("comments_url")
    if comments_url:
        comments_response = requests.get(comments_url, headers=headers)
        if comments_response.status_code == 200:
            for comment in comments_response.json():
                comments.append({
                    "author": comment.get("user", {}).get("login", "Unknown"),
                    "date": comment.get("created_at", "Unknown"),
                    "body": comment.get("body", "")
                })

    return {
        "title": title,
        "author": author,
        "date": date,
        "body": body,
        "comments": comments,
        "url": url
    }

def format_output(issue_data):
    """Format issue data into git log-like output"""
    output = []
    output.append(f"Issue #{issue_data['url'].split('/')[-1]}")
    output.append(f"Author: {issue_data['author']}")
    output.append(f"Date:   {issue_data['date']}")
    output.append(f"Title:  {issue_data['title']}")
    output.append(f"URL:    {issue_data['url']}")
    output.append("\nBody:")
    output.append(issue_data['body'] + "\n")

    if issue_data['comments']:
        output.append("Comments:")
        for comment in issue_data['comments']:
            output.append(f"• {comment['date']} {comment['author']}:")
            output.append(f"  {comment['body']}\n")

    output.append("-" * 80 + "\n")
    return "\n".join(output)

def main():
    # Get all open issue numbers
    issue_numbers = get_issue_numbers(BASE_URL, REPO_OWNER, REPO_NAME)
    print(f"Found {len(issue_numbers)} open issues. Processing...")

    # Process each issue
    output = []
    for num in issue_numbers:
        url = f"{BASE_URL}/api/v1/repos/{REPO_OWNER}/{REPO_NAME}/issues/{num}"  # Corrected URL
        issue_data = parse_issue_page(url)
        if issue_data:
            output.append(format_output(issue_data))

    # Write to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print(f"Output written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()