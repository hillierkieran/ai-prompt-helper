import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://git.oraclecms.com:3000"
PROJECT_URL = f"{BASE_URL}/Kieran/LoneWorkerRebuild/projects/8"
REPO_OWNER = "Kieran"
REPO_NAME = "LoneWorkerRebuild"
OUTPUT_FILE = "./tmp/issues_kanban.txt"
API_TOKEN = "ad7bbb0e7563c44e5953563dce11bfba1cce7873"

headers = {"Authorization": f"token {API_TOKEN}"}

def parse_issue_page(url):
    """Fetch issue details using the Gitea API and return structured data"""
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch issue page. HTTP Status: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    issue = response.json()
    title = issue.get("title", "Untitled")
    author = issue.get("user", {}).get("login", "Unknown")
    date = issue.get("created_at", "Unknown")
    body = issue.get("body", "")
    comments = []

    comments_url = issue.get("comments_url")
    if comments_url:
        print(f"Fetching comments from: {comments_url}")
        comments_response = requests.get(comments_url, headers=headers)
        if comments_response.status_code == 200:
            for comment in comments_response.json():
                comments.append({
                    "author": comment.get("user", {}).get("login", "Unknown"),
                    "date": comment.get("created_at", "Unknown"),
                    "body": comment.get("body", "")
                })
            print(f"Comments fetched: {comments}")

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
    output.append(f"Issue:  #{issue_data['url'].split('/')[-1]}")
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

def get_column_issues():
    """Scrape project page to get open issues grouped by columns"""
    print(f"Fetching project page from: {PROJECT_URL}")

    # Use the correct cookies from the browser
    cookies = {
        "i_like_gitea": "505c83e32c4ff8f7",
        "lang": "en-US",
        "_csrf": "6e4cSgZiid8lwnxbvX3vgY6t-sU6MTc0OTc5MDExNDYyNTY2MjUyMg"
    }

    # Send the request with cookies
    response = requests.get(PROJECT_URL, headers=headers, cookies=cookies)
    if response.status_code != 200:
        print(f"Failed to fetch project page. Status: {response.status_code}")
        print(f"Response: {response.text}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    columns = soup.find_all('div', class_='project-column')
    column_issues = {}

    print("Parsing columns...")
    for column in columns:
        # Extract column title
        title_div = column.find('div', class_='project-column-title-label')
        if not title_div:
            print("Column title not found, skipping...")
            continue
        title = title_div.get_text(strip=True)

        # Extract open issue numbers
        issue_cards = column.find_all('div', class_='issue-card')
        issue_numbers = []
        for card in issue_cards:
            # Check if the issue is open
            if card.find('svg', class_='octicon-issue-opened'):
                link = card.find('a', class_='issue-card-title')
                if link and link.has_attr('href'):
                    href = link['href']
                    issue_number = href.split('/')[-1]
                    if issue_number.isdigit():
                        issue_numbers.append(int(issue_number))

        column_issues[title] = issue_numbers

    return column_issues

def main():
    column_issues = get_column_issues()
    if not column_issues:
        print("No columns found. Exiting.")
        return

    output = []
    for column, issues in column_issues.items():
        print(f"Processing column: {column}")
        output.append(f"### Column: {column} ###\n")
        for issue_num in issues:
            url = f"{BASE_URL}/api/v1/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_num}"
            print(f"Processing issue #{issue_num}")
            issue_data = parse_issue_page(url)
            if issue_data:
                output.append(format_output(issue_data))
        output.append("\n" + "=" * 80 + "\n")

    print(f"Writing output to file: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print(f"Grouped issues written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()