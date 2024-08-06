import requests
import os
import json
from openai import OpenAI

# 各環境変数を定数化
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPOSITORY = os.getenv("REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER"))
PRJ_NAME = os.getenv("PRJ_NAME")
PR_API_URL = f'https://api.github.com/repos/{REPOSITORY}/pulls/{PR_NUMBER}'


def get_pr_diff():
    print('get_pr_diff')
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    diff_response = requests.get(PR_API_URL, headers=headers)
    return diff_response.text


def get_openai_review(prompt):
    print('get_openai_review')
    client = OpenAI(api_key=OPENAI_API_KEY)
    # レスポンスをjson、modelにGPT-4 Turboを指定
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        response_format={"type": "json_object"},
        model="gpt-4-1106-preview",
    )
    review_result = chat_completion.choices[0].message.content
    return review_result


def create_prompt(code_diff):
    print('create_prompt')
    prompt = (f'Review the following code:\n\n{code_diff}\n\n'
              '- Be sure to comment on areas for improvement.\n'
              '- Please make review comments in Japanese.\n'
              '- Ignore the use of "self." when using variables and functions.\n'
              '- Please prefix your review comments with one of the following labels "MUST:","IMO:","NITS:".\n'
              '  - MUST: must be modified\n'
              '  - IMO: personal opinion or minor proposal\n'
              '  - NITS: Proposals that do not require modification\n'
              '- The following json format should be followed.\n'
              '{"files":[{"fileName":"<file_name>","reviews": [{"lineNumber":<line_number>,"reviewComment":"<review '
              'comment>"}]}]}\n'
              '- If there is no review comment, please answer {"files":[]}\n')
    prompt += create_ignore_pr_reviews_prompt()
    return prompt


def create_ignore_pr_reviews_prompt():
    print('create_ignore_pr_reviews_prompt')
    url = f'{PR_API_URL}/comments'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    comments = response.json()
    if len(comments) == 0:
        return ""
    ignore_prompt = '- However, please ensure the content does not duplicate the following existing comments:\n'
    for comment in comments:
        body = comment['body']
        path = comment.get('path')
        line = comment.get('line') or comment.get('original_line')
        ignore_prompt += f'  - file "{path}", line {line}: {body}\n'
    return ignore_prompt


def save_result(result):
    print('save_result')
    with open(f"./results/{PRJ_NAME}.json", "w") as file:
        print(result, file=file)


code_diff = get_pr_diff()
prompt = create_prompt(code_diff)
review_json = get_openai_review(prompt)
save_result(review_json)
# print(json.dumps(review_json, indent=2))
