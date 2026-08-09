#!/usr/bin/env python3
"""
ERP Test - Student Repository Link Generator

This script generates fork URLs for students to use their own GitHub accounts.
No repositories are created by the instructor - students fork the template themselves.

Usage:
    python create_repos.py
    
This will generate a CSV file with fork URLs to share with students.
"""

import csv
import sys
from typing import Dict, List
import json
import requests

# Configuration - UPDATE THESE VALUES
GITHUB_TOKEN = "your_personal_access_token_here"  # Your GitHub PAT (optional, for validation)
TEMPLATE_REPO_OWNER = "your-github-username"  # Your GitHub username or organization
TEMPLATE_REPO_NAME = "erp-coding-test"  # Name of your template repository
STUDENTS_CSV = "students.csv"  # CSV with columns: name,email,github_username

HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}

if GITHUB_TOKEN and GITHUB_TOKEN != "your_personal_access_token_here":
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"


def check_github_user(username: str) -> bool:
    """Check if a GitHub username exists"""
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url, headers=HEADERS)
    return response.status_code == 200


def get_fork_url(owner: str, repo_name: str, student_username: str) -> str:
    """Generate the fork URL for a student"""
    return f"https://github.com/{owner}/{repo_name}/fork?to={student_username}"


def get_repo_url(student_username: str, repo_name: str) -> str:
    """Get the expected repository URL after forking"""
    return f"https://github.com/{student_username}/{repo_name}"


def get_codespaces_url(student_username: str, repo_name: str) -> str:
    """Get the Codespaces URL for the student's forked repository"""
    return f"https://github.com/codespaces/new?repo={student_username}%2F{repo_name}"


def main():
    print("🎓 ERP Test - Student Fork URL Generator")
    print("=" * 60)
    print("\nThis tool generates fork URLs for students to use their own GitHub accounts.")
    print("Students will fork the template repo to their personal accounts.\n")
    
    # Optional: Validate token if provided
    if GITHUB_TOKEN and GITHUB_TOKEN != "your_personal_access_token_here":
        test_url = "https://api.github.com/user"
        response = requests.get(test_url, headers=HEADERS)
        if response.status_code == 200:
            print(f"✅ GitHub token validated for user: {response.json().get('login', 'Unknown')}")
        else:
            print("⚠️  GitHub token validation failed. Continuing without token validation.")
    else:
        print("ℹ️  No GitHub token provided. Skipping validation (optional).")
    
    print(f"📦 Template Repository: {TEMPLATE_REPO_OWNER}/{TEMPLATE_REPO_NAME}")
    print("=" * 60)
    
    # Read students from CSV
    try:
        with open(STUDENTS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            students = list(reader)
    except FileNotFoundError:
        print(f"\n❌ File '{STUDENTS_CSV}' not found.")
        print("\nPlease create a CSV file with the following columns:")
        print("  name,email,github_username")
        print("\nExample:")
        print("  John Doe,john@example.com,johndoe")
        print("  Jane Smith,jane@example.com,janesmith")
        sys.exit(1)
    
    if not students:
        print("❌ No students found in CSV file.")
        sys.exit(1)
    
    print(f"\n📊 Found {len(students)} students in CSV\n")
    print("=" * 60)
    
    # Statistics
    valid_count = 0
    invalid_count = 0
    invalid_users = []
    results = []
    
    for idx, student in enumerate(students, 1):
        name = student.get("name", "Unknown").strip()
        email = student.get("email", "").strip()
        username = student.get("github_username", "").strip()
        
        print(f"\n[{idx}/{len(students)}] Processing: {name} (@{username})")
        
        # Validate required fields
        if not username:
            print(f"   ⚠️  Skipping: No GitHub username provided")
            invalid_count += 1
            results.append({
                "student": name,
                "email": email,
                "username": "",
                "status": "skipped_no_username",
                "fork_url": "",
                "repo_url": "",
                "codespaces_url": ""
            })
            continue
        
        # Check if GitHub user exists (only if token is provided)
        if GITHUB_TOKEN and GITHUB_TOKEN != "your_personal_access_token_here":
            if not check_github_user(username):
                print(f"   ❌ GitHub user '@{username}' does not exist")
                invalid_users.append(f"{name} (@{username})")
                invalid_count += 1
                results.append({
                    "student": name,
                    "email": email,
                    "username": username,
                    "status": "invalid_user",
                    "fork_url": "",
                    "repo_url": "",
                    "codespaces_url": ""
                })
                continue
        
        # Generate URLs
        fork_url = get_fork_url(TEMPLATE_REPO_OWNER, TEMPLATE_REPO_NAME, username)
        repo_url = get_repo_url(username, TEMPLATE_REPO_NAME)
        codespaces_url = get_codespaces_url(username, TEMPLATE_REPO_NAME)
        
        print(f"   ✅ Valid GitHub username")
        print(f"   🔗 Fork URL: {fork_url}")
        print(f"   📁 Expected Repo: {repo_url}")
        
        valid_count += 1
        results.append({
            "student": name,
            "email": email,
            "username": username,
            "status": "valid",
            "fork_url": fork_url,
            "repo_url": repo_url,
            "codespaces_url": codespaces_url
        })
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Valid Students: {valid_count}")
    print(f"❌ Invalid/Skipped: {invalid_count}")
    
    if invalid_users:
        print(f"\n⚠️  Invalid GitHub users (not found on GitHub):")
        for user in invalid_users:
            print(f"   - {user}")
    
    # Save results as JSON
    with open("student_fork_urls.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed results saved to: student_fork_urls.json")
    
    # Generate CSV with fork URLs for distribution
    with open("student_fork_instructions.csv", "w", encoding="utf-8") as f:
        f.write("name,email,github_username,fork_url,repo_url,codespaces_url,status\n")
        for r in results:
            f.write(f"{r['student']},{r['email']},{r['username']},{r['fork_url']},{r['repo_url']},{r['codespaces_url']},{r['status']}\n")
    
    print(f"📧 Fork instructions CSV saved to: student_fork_instructions.csv")
    
    # Generate email template
    print("\n" + "=" * 60)
    print("📧 EMAIL TEMPLATE FOR STUDENTS")
    print("=" * 60)
    
    email_template = f"""
Subject: ERP Developer Coding Test - Instructions

Dear Student,

You have been invited to participate in the ERP Developer Coding Test.

IMPORTANT: You will use YOUR OWN GitHub account for this test.

TEST DETAILS:
- Duration: Self-paced (no strict time limit)
- Platform: GitHub with Codespaces
- Submission: Push your completed code to your forked repository

INSTRUCTIONS:

1. Click on your personalized fork URL below to fork the test repository to your GitHub account.

2. After forking, open the repository in Codespaces to start coding.

3. Complete all 5 questions as described in the README.md file.

4. Commit your code regularly and push to the 'main' branch when done.

YOUR PERSONALIZED LINKS:
- Fork URL: {{FORK_URL}}
- Your Repository: {{REPO_URL}}
- Open in Codespaces: {{CODESPACES_URL}}

GRADING:
After you push your final code to the main branch, GitHub Actions will automatically:
- Run all tests
- Grade your submissions
- Generate a score report

Your instructor will collect the results afterward.

Good luck!

Best regards,
Your Instructor
"""
    
    print(email_template)
    
    # Save email template
    with open("email_template.txt", "w", encoding="utf-8") as f:
        f.write(email_template)
    print(f"\n💾 Email template saved to: email_template.txt")
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("\nNEXT STEPS:")
    print("1. Review 'student_fork_instructions.csv' for all student links")
    print("2. Send personalized emails to each student with their fork URL")
    print("3. Students fork the repo and complete the test")
    print("4. After completion, run collect_scores.py to gather all results")
    print("=" * 60)


if __name__ == "__main__":
    main()
