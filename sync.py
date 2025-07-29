import os
import requests
import json
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 飞书API配置
APP_ID = os.getenv('FEISHU_APP_ID')
APP_SECRET = os.getenv('FEISHU_APP_SECRET')
TABLE_ID = os.getenv('FEISHU_TABLE_ID')
BASE_URL = "https://open.feishu.cn/open-apis/bitable/v1"

def get_feishu_token():
    """获取飞书访问令牌"""
    url = f"{BASE_URL}/apps/{TABLE_ID}/tables?page_size=1"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        if result.get("code") != 0:
            logger.error(f"Token获取失败: {result.get('msg')}")
            return None
        return result.get('tenant_access_token')
    except Exception as e:
        logger.error(f"Token请求异常: {str(e)}")
        return None

def get_table_records(token, table_id):
    """获取表格记录"""
    url = f"{BASE_URL}/apps/{TABLE_ID}/tables/{table_id}/records"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {"page_size": 200}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != 0:
            logger.error(f"数据获取失败: {data.get('msg')}")
            return []
        
        # 调试输出
        logger.info(f"成功获取 {len(data.get('data', {}).get('items', []))} 条记录")
        return data.get('data', {}).get('items', [])
    except Exception as e:
        logger.error(f"记录请求异常: {str(e)}")
        return []

def generate_md(record):
    """生成Markdown文件"""
    fields = record.get('fields', {})
    
    # 必需字段检查
    required_fields = ['title', 'content', 'date', 'slug']
    if not all(field in fields for field in required_fields):
        logger.warning(f"记录缺少必需字段: {record.get('record_id')}")
        return
    
    # 创建目录
    os.makedirs("_posts", exist_ok=True)
    
    # 文件名格式: YYYY-MM-DD-slug.md
    date_obj = datetime.strptime(fields['date'], '%Y-%m-%d')
    filename = f"{date_obj.strftime('%Y-%m-%d')}-{fields['slug']}.md"
    
    # 文件内容
    content = f"""---
layout: post
title: "{fields['title']}"
date: {fields['date']}
category: {fields.get('category', '未分类')}
---

{fields['content']}
"""
    
    # 写入文件
    filepath = os.path.join("_posts", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"生成文件: {filename}")

def main():
    """主函数"""
    logger.info("开始同步飞书数据...")
    
    # 获取访问令牌
    token = get_feishu_token()
    if not token:
        logger.error("无法获取飞书访问令牌，终止同步")
        return
    
    # 获取表格ID（需要先获取表格列表）
    tables_url = f"{BASE_URL}/apps/{TABLE_ID}/tables"
    headers = {"Authorization": f"Bearer {token}"}
    tables_res = requests.get(tables_url, headers=headers)
    tables_data = tables_res.json()
    
    if tables_data.get("code") != 0:
        logger.error(f"获取表格列表失败: {tables_data.get('msg')}")
        return
    
    # 假设使用第一个表格
    if not tables_data.get('data', {}).get('items'):
        logger.error("未找到任何表格")
        return
    
    table_id = tables_data['data']['items'][0]['table_id']
    logger.info(f"使用表格ID: {table_id}")
    
    # 获取记录
    records = get_table_records(token, table_id)
    if not records:
        logger.warning("未获取到任何记录")
        return
    
    # 生成Markdown文件
    for record in records:
        generate_md(record)
    
    logger.info(f"同步完成，共处理 {len(records)} 条记录")

if __name__ == "__main__":
    main()
