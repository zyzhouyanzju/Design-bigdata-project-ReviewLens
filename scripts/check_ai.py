"""Check API connectivity without displaying credentials or request contents."""
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / '.local_packages'))
from openai import OpenAI

with (ROOT / '.streamlit' / 'secrets.toml').open('rb') as f:
    key = tomllib.load(f)['DEEPSEEK_API_KEY']
try:
    response = OpenAI(api_key=key, base_url='https://api.deepseek.com', timeout=15, max_retries=0).chat.completions.create(
        model='deepseek-flash', messages=[{'role':'user','content':'Hi'}], max_tokens=16
    )
    print('RESULT=success')
except Exception as exc:
    print('ERROR_TYPE=' + type(exc).__name__)
    print('STATUS=' + str(getattr(exc, 'status_code', None)))
    print('CAUSE_TYPE=' + (type(exc.__cause__).__name__ if exc.__cause__ else 'None'))
    body = getattr(exc, 'body', None)
    if isinstance(body, dict):
        error = body.get('error', body)
        if isinstance(error, dict): print('ERROR_CODE=' + str(error.get('code', 'unknown')))
