import os
import sys
import json
import csv
import argparse
import requests
from datetime import datetime
import zipfile
import io

# --- PDF Generation using built-in libraries (No fpdf/reportlab needed) ---
def generate_simple_pdf_text(scores):
    """Generates a text-based report that can be easily converted or read."""
    lines = []
    lines.append("=" * 80)
    lines.append("ERP CODING TEST - SCORE REPORT")
    lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    
    total_students = len(scores)
    avg_score = sum(s['total_score'] for s in scores) / total_students if total_students > 0 else 0
    max_score = max(s['total_score'] for s in scores) if total_students > 0 else 0
    
    lines.append(f"Total Students: {total_students}")
    lines.append(f"Average Score:  {avg_score:.2f}")
    lines.append(f"Highest Score:  {max_score}")
    lines.append("-" * 80)
    
    # Header
    header = f"{'Name':<25} {'Username':<20} {'Total':<6} {'Q1':<4} {'Q2':<4} {'Q3':<4} {'Q4':<4} {'Q5':<4}"
    lines.append(header)
    lines.append("-" * 80)
    
    for s in scores:
        row = f"{s['student_name'][:24]:<25} {s['github_username'][:19]:<20} {s['total_score']:<6} {s['q1_backend']:<4} {s['q2_database']:<4} {s['q3_frontend']:<4} {s['q4_cicd']:<4} {s['q5_prompt']:<4}"
        lines.append(row)
        
    lines.append("=" * 80)
    return "\n".join(lines)

def download_artifact_score(repo_owner, repo_name, token, workflow_run_id=None):
    """Downloads the score.json artifact from a specific GitHub repository."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    if not workflow_run_id:
        # Find latest successful workflow run
        runs_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs?event=push&status=success&per_page=1"
        try:
            r = requests.get(runs_url, headers=headers)
            r.raise_for_status()
            data = r.json()
            
            if data['total_count'] > 0:
                workflow_run_id = data['workflow_runs'][0]['id']
            else:
                # Fallback to workflow_dispatch
                runs_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs?event=workflow_dispatch&status=success&per_page=1"
                r = requests.get(runs_url, headers=headers)
                r.raise_for_status()
                data = r.json()
                if data['total_count'] > 0:
                    workflow_run_id = data['workflow_runs'][0]['id']
                else:
                    return None
        except Exception as e:
            print(f"   ⚠️  Error finding workflow runs: {e}")
            return None

    artifacts_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{workflow_run_id}/artifacts"
    try:
        r = requests.get(artifacts_url, headers=headers)
        r.raise_for_status()
        data = r.json()
        
        if data['total_count'] == 0:
            return None
            
        score_artifact = None
        for artifact in data['artifacts']:
            if artifact['name'] == 'score-result':
                score_artifact = artifact
                break
        
        if not score_artifact:
            return None

        download_url = score_artifact['archive_download_url']
        r_zip = requests.get(download_url, headers=headers)
        r_zip.raise_for_status()
        
        z = zipfile.ZipFile(io.BytesIO(r_zip.content))
        if 'score.json' in z.namelist():
            return json.loads(z.read('score.json'))
        return None

    except Exception as e:
        print(f"   ⚠️  Error downloading artifact: {e}")
        return None

def fetch_scores_github_mode(students_csv, token):
    scores = []
    print(f"\n📊 Fetching scores from GitHub for students in {students_csv}...")
    
    with open(students_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get('github_username', '').strip()
            if not username:
                continue
            
            repo_name = "erp-coding-test" 
            full_repo = f"{username}/{repo_name}"
            
            print(f"[{reader.line_num}] Checking {full_repo}...")
            
            score_data = download_artifact_score(username, repo_name, token)
            
            if score_data:
                print(f"   ✅ Score found: {score_data.get('total_score', 'N/A')}")
                score_entry = {
                    'student_name': row.get('name', 'Unknown'),
                    'email': row.get('email', 'Unknown'),
                    'github_username': username,
                    'repo_url': f"https://github.com/{full_repo}",
                    'total_score': score_data.get('total_score', 0),
                    'q1_backend': score_data.get('breakdown', {}).get('q1_backend', 0),
                    'q2_database': score_data.get('breakdown', {}).get('q2_database', 0),
                    'q3_frontend': score_data.get('breakdown', {}).get('q3_frontend', 0),
                    'q4_cicd': score_data.get('breakdown', {}).get('q4_cicd', 0),
                    'q5_prompt': score_data.get('breakdown', {}).get('q5_prompt', 0),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                scores.append(score_entry)
            else:
                print(f"   ⚠️  No score.json artifact found (Workflow may not have finished or failed).")
                
    return scores

def generate_csv(scores, output_path):
    if not scores:
        print("⚠️  No scores to write to CSV.")
        return
        
    keys = scores[0].keys()
    with open(output_path, 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(scores)
    print(f"✅ CSV report generated: {output_path}")

def generate_pdf_report(scores, output_path):
    """Generates a .txt report named .pdf to avoid dependencies, or you can install fpdf2 later."""
    if not scores:
        print("⚠️  No scores to generate report.")
        return
    
    content = generate_simple_pdf_text(scores)
    
    # We save as .txt to ensure it opens correctly without special libraries
    txt_path = output_path.replace('.pdf', '.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"✅ Text report generated: {txt_path}")
    print("   (Note: To get a real .pdf file, run: pip install fpdf2)")

def main():
    parser = argparse.ArgumentParser(description="Collect scores from student repos")
    parser.add_argument("--github-mode", action="store_true", help="Fetch scores via GitHub API")
    parser.add_argument("--students-csv", required=True, help="Path to students.csv")
    parser.add_argument("--token", required=True, help="GitHub Personal Access Token")
    parser.add_argument("--output-dir", default="./reports", help="Output directory for reports")
    
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    scores = []
    if args.github_mode:
        scores = fetch_scores_github_mode(args.students_csv, args.token)
    else:
        print("Local mode not implemented in this update. Please use --github-mode.")
        sys.exit(1)

    if not scores:
        print("\n⚠️  No scores collected. Check if students have pushed and workflows succeeded.")
        return

    csv_path = os.path.join(args.output_dir, "consolidated_scores.csv")
    pdf_path = os.path.join(args.output_dir, "consolidated_report.pdf")
    
    generate_csv(scores, csv_path)
    generate_pdf_report(scores, pdf_path)
    
    print("\n🎉 Collection complete!")

if __name__ == "__main__":
    main()
