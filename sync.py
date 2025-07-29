import os
import requests
import json
from datetime import datetime

# 飞书API配置
APP_ID = os.getenv('FEISHU_APP_ID')
APP_SECRET = os.getenv('FEISHU_APP_SECRET')
TABLE_ID = os.getenv('FEISHU_TABLE_ID')

# 获取飞书Token
def get_feishu_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    response = requests.post(url, headers=headers, json=data)
    return response.json().get('tenant_access_token')

# 获取表格数据
def get_records(token):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_ID}/tables/表格ID/records"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    return response.json().get('data').get('items')

# 生成Markdown文件
def generate_md(record):
    fields = record.get('fields')
    date_str = fields.get('date')
    slug = fields.get('slug')
    filename = f"{date_str}-{slug}.md"
    
    content = f"""---
layout: post
title: "{fields.get('title')}"
date: {date_str}
category: {fields.get('category')}
---
{fields.get('content')}
"""
    
    with open(f"_posts/{filename}", "w") as f:
        f.write(content)

# 主流程
if __name__ == "__main__":
    token = get_feishu_token()
    records = get_records(token)
    for record in records:
        generate_md(record)
