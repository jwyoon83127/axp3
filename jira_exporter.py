import os
import re
import csv
import requests
from requests.auth import HTTPBasicAuth

def extract_customer(summary):
    """이슈 제목에서 [고객사명] 형식의 텍스트를 추출합니다."""
    match = re.search(r'\[([^\]]+)\]', summary)
    return match.group(1).strip() if match else "미분류"

def extract_assignee_from_body(body):
    """이슈 본문에서 '담당자: 이름' 또는 '작성자: 이름' 형식을 추출합니다."""
    if not body:
        return ""
    # 담당자 또는 작성자 다음에 오는 텍스트를 찾되, 다음 주요 키워드 집합 전까지 캡처
    keywords = ["실행빈도", "소요시간", "사용 프로그램", "데이터 소스", "결과물 형태", "자동화 여부", "프로세스", "AI 툴 추천", "난이도", "업무 설명"]
    pattern = r'(?:담당자|작성자):\s*(.*?)(?=' + '|'.join(keywords) + r'|$)'
    match = re.search(pattern, body, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        # 불필요한 불용어 및 특수문자 제거
        name = re.sub(r'[:;]', '', name).strip()
        return name
    return ""

def extract_text_from_adf(node):
    """Jira ADF(Atlassian Document Format) JSON 구조에서 순수 텍스트만 추출합니다."""
    if not node:
        return ""
    
    text_parts = []
    
    if isinstance(node, dict):
        node_type = node.get('type')
        
        # 텍스트 노드인 경우
        if node_type == 'text':
            # 텍스트 자체에 포함된 줄바꿈 제거
            raw_text = node.get('text', '')
            return raw_text.replace('\n', ' ').replace('\r', ' ')
        
        # 내용을 재귀적으로 처리
        if 'content' in node:
            for child in node['content']:
                text_parts.append(extract_text_from_adf(child))
            
            # 문단이면 끝에 줄바꿈 대신 공백 추가 (한 줄 출력을 위해)
            if node_type == 'paragraph':
                text_parts.append(' ')
    
    return "".join(text_parts).strip()

def export_jira_as_data_to_csv():
    """Jira AS 프로젝트 데이터를 수집하여 CSV로 추출합니다."""
    # Jira 서버 정보 및 인증
    JIRA_URL = 'https://humuson.atlassian.net'
    user_email = "chorani@humuson.com"
    # 기존 코드의 토큰을 기본값으로 사용 (환경 변수 권장)
    api_token = os.environ.get('JIRA_API_TOKEN', 'YOUR_JIRA_API_TOKEN_HERE')
    
    auth = HTTPBasicAuth(user_email, api_token)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Jira 프로젝트 키 및 기간 설정 (AS 프로젝트 전용)
    project_key = 'AS'
    start_date = "2022-01-01"
    end_date = "2026-12-31"
    
    filename = f"jira_{project_key}_full_data.csv"

    try:
        print(f"[{project_key}] 프로젝트 데이터를 수집 중입니다... (계정: {user_email})")

        # 1. 이슈 검색 (Jira Cloud V3 Search API)
        search_url = f"{JIRA_URL}/rest/api/3/search/jql"
        jql = f'project = "{project_key}" AND created >= "{start_date}" AND created <= "{end_date}" ORDER BY created ASC'
        
        all_issues = []
        next_page_token = None
        max_results = 50

        while True:
            payload = {
                "jql": jql,
                "maxResults": max_results,
                "fields": ["summary", "description", "created", "parent", "issuetype", "status", "resolutiondate", "assignee"]
            }
            
            if next_page_token:
                payload["nextPageToken"] = next_page_token
            
            response = requests.post(search_url, json=payload, auth=auth, headers=headers)
            
            if response.status_code != 200:
                print(f"검색 API 호출 실패: {response.status_code} - {response.text}")
                return

            data = response.json()
            issues = data.get('issues', [])
            if not issues:
                break
                
            all_issues.extend(issues)
            print(f"현재 {len(all_issues)}개 이슈 확보 중...")
            
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break

        if not all_issues:
            print(f"{project_key} 프로젝트에 조회된 이슈가 없습니다.")
            return

        print(f"\n총 {len(all_issues)}개의 이슈를 찾았습니다. 상세 데이터를 수집하여 CSV로 작성합니다.")

        # 2. CSV 파일 작성
        csv_path = os.path.join(os.path.dirname(__file__), filename)
        with open(csv_path, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['이슈키', '이슈유형', '부모이슈', '상태', '고객사', '제목', '이슈본문', '댓글작성자', '댓글내용', '생성일', '완료일', '담당자'])

            for issue in all_issues:
                issue_key = issue['key']
                fields = issue['fields']
                summary = fields.get('summary', '')
                summary = summary.replace('\n', ' ').replace('\r', ' ')
                customer = extract_customer(summary)
                
                # 이슈 유형 추출 (Epic 여부 확인용)
                issue_type = fields.get('issuetype', {}).get('name', 'N/A')
                
                # 부모 이슈 키 추출 (Epic 또는 상위 Task)
                parent_key = fields.get('parent', {}).get('key', '없음')
                
                # 상태 정보 추출
                status = fields.get('status', {}).get('name', 'N/A')
                
                description_data = fields.get('description')
                description = extract_text_from_adf(description_data)

                created_date = fields.get('created', '')
                resolution_date = fields.get('resolutiondate', '')
                if resolution_date:
                    resolution_date = resolution_date.split('T')[0]

                assignee = fields.get('assignee')
                official_assignee = assignee.get('displayName', '미배정') if assignee else '미배정'
                
                # 이슈 본문에서 담당자 정보 추출 시도
                extracted_assignee = extract_assignee_from_body(description)
                assignee_name = extracted_assignee if extracted_assignee else official_assignee

                # 3. 이슈별 댓글 가져오기
                comments_url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/comment"
                comm_res = requests.get(comments_url, auth=auth, headers=headers)
                
                comments = []
                if comm_res.status_code == 200:
                    comments = comm_res.json().get('comments', [])

                if comments:
                    for comment in comments:
                        author_name = comment.get('author', {}).get('displayName', 'Unknown')
                        body_content = extract_text_from_adf(comment.get('body'))
                        writer.writerow([
                            issue_key,
                            issue_type,
                            parent_key,
                            status,
                            customer,
                            summary,
                            description,
                            author_name,
                            body_content,
                            created_date,
                            resolution_date,
                            assignee_name
                        ])
                else:
                    writer.writerow([
                        issue_key,
                        issue_type,
                        parent_key,
                        status,
                        customer,
                        summary,
                        description,
                        "N/A",
                        "댓글 없음",
                        created_date,
                        resolution_date,
                        assignee_name
                    ])

        print(f"\n성공적으로 저장되었습니다: {os.path.abspath(csv_path)}")

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    export_jira_as_data_to_csv()
