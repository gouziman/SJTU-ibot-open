import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import time  
import schedule
from datetime import datetime, timedelta, timezone
import os
CANVAS_TOKEN = os.getenv('CANVAS_TOKEN')
SC_KEY = os.getenv('SC_KEY')

# ================= 配置区 =================
SERVER_CHAN_URL = f"https://sctapi.ftqq.com/{SC_KEY}.send"
CANVAS_URL = "https://oc.sjtu.edu.cn"
# ==========================================

def print_log(msg):
    """带时间戳的日志打印"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")

def push_to_wechat(title, content):
    """统一的 Server酱推送组件"""
    try:
        data = {"title": title, "desp": content}
        res = requests.post(SERVER_CHAN_URL, data=data, timeout=10)
        if res.status_code == 200:
            print_log(f">>> 微信推送已发出: {title}")
        else:
            print_log(f">>> 推送失败，状态码: {res.status_code}")
    except Exception as e:
        print_log(f">>> 推送接口报错: {e}")

def handle_error(error_msg):
    """处理错误并发送错误报告"""
    error_title = "【ibot错误报告】系统异常"
    error_content = f"**错误信息：** {error_msg}\n\n**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n**请检查系统配置和网络连接**"
    print_log(f"【错误报告】: {error_msg}")
    push_to_wechat(error_title, error_content)

def get_history():
    """读取历史记录"""
    try:
        with open("history.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def write_history(item_id):
    """追加历史记录"""
    with open("history.txt", "a", encoding="utf-8") as f:
        f.write(f"{item_id}\n")

# ----------------- 任务1：交大官网通知爬虫 -----------------
def fetch_sjtu_news():
    print_log("开始检查：交大官网通知")
    url = "https://www.sjtu.edu.cn/tg/index.html"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.select('li')
        if not news_items:
            news_items = soup.find_all('li', class_='item')

        history_content = get_history()
        
        for item in news_items:
            a_tag = item.find('a')
            if not a_tag: continue
            
            title = item.get_text(strip=True)
            link = a_tag.get('href', '')
            if not link.startswith('http'): link = "https://www.sjtu.edu.cn" + link
            
            # --- 去重 ---
            if title in history_content:
                continue
            
            print_log(f"发现新官网通知: {title}")
            content = f"**官网标题：** {title}\n\n**详情链接：** [点击跳转]({link})"
            title = f"【官网】{title}"
            push_to_wechat(title, content)
            write_history(title)

    except Exception as e:
        error_msg = f"官网爬取异常: {e}"
        handle_error(error_msg)

# ----------------- 任务2：Canvas 智能助理 -----------------
def fetch_canvas_updates():
    print_log("开始检查：Canvas系统 (公告及作业DDL)")
    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
    
    # 每次运行前获取一次历史记录
    history_content = get_history()

    try:
        # 1. 获取所有进行中的课程 (enrollment_state=active)
        courses_res = requests.get(f"{CANVAS_URL}/api/v1/courses", headers=headers, params={"enrollment_state": "active"}, timeout=15)
        courses_res.raise_for_status()
        courses = courses_res.json()

        for course in courses:
            course_id = course.get('id')
            course_name = course.get('name', '未命名课程')
            if not course_id: continue

            # --- A. 检查课程公告 (Announcements) ---
            ann_params = {"context_codes[]": f"course_{course_id}", "per_page": 5} # 只查最近5条，防止第一次运行爆炸
            ann_res = requests.get(f"{CANVAS_URL}/api/v1/announcements", headers=headers, params=ann_params, timeout=10)
            
            if ann_res.status_code == 200:
                for ann in ann_res.json():
                    ann_id = f"canvas_ann_{ann.get('id')}"
                    
                    if ann_id not in history_content:
                        print_log(f"发现新课程公告: {ann.get('title')}")
                        content = f"**课程：** {course_name}\n\n**公告标题：** {ann.get('title')}\n\n**详情链接：** [点击查看]({ann.get('html_url')})"
                        title = f"【Canvas】{ann.get('title')}"
                        push_to_wechat(title, content)
                        # 同时存储ID、标题和链接到历史记录
                        history_entry = f"{ann_id}|{ann.get('title')}|{ann.get('html_url')}"
                        write_history(history_entry)
            
            # --- B. 检查作业和 DDL (Assignments) ---
            # include[]=submission 会把你的提交状态一并返回，避免已交的作业还报警
            ass_res = requests.get(f"{CANVAS_URL}/api/v1/courses/{course_id}/assignments", headers=headers, params={"include[]": "submission"}, timeout=10)
            
            if ass_res.status_code == 200:
                for assign in ass_res.json():
                    # 判断 1: 有没有 DDL?
                    due_at_str = assign.get('due_at')
                    if not due_at_str: continue 
                    
                    # 判断 2: 你交了吗? (只要不是未提交就放过它)
                    submission = assign.get('submission', {})
                    if submission.get('workflow_state') != 'unsubmitted': 
                        continue

                    # 将 Canvas 的 UTC 时间字符串转换为 Python 时间对象
                    due_utc = datetime.strptime(due_at_str, "%Y-%m-%dT%H:%M:%SZ")
                    now_utc = datetime.now(timezone.utc) 
                    
                    time_left = due_utc - now_utc
                    hours_left = time_left.total_seconds() / 3600

                    # 已经过期了就不提醒了
                    if hours_left <= 0: continue

                    # 判断 3: 触发哪个梯队?
                    tag = None
                    if hours_left <= 6:
                        tag = "6h"
                    elif hours_left <= 48:
                        tag = "48h"
                    
                    if tag:
                        alert_id = f"canvas_alert_{tag}_{assign.get('id')}"
                        
                        # 判断 4: 这个梯队提醒过了吗?
                        if alert_id not in history_content:
                            due_local = due_utc + timedelta(hours=8) # 换算成北京时间发给你看
                            print_log(f"触发 {tag} DDL预警: {assign.get('title')}")
                            
                            content = (
                                f"**课程：** {course_name}\n\n"
                                f"**作业：** {assign.get('title')}\n\n"
                                f"**截止时间：** {due_local.strftime('%m-%d %H:%M')} (剩余约 {int(hours_left)} 小时)\n\n"
                                f"**直达链接：** [火速去写]({assign.get('html_url')})"
                            )
                            push_to_wechat(f"🔥【作业预警-{tag}】", content)
                            write_history(alert_id)
                            
    except Exception as e:
        error_msg = f"Canvas层级异常: {e}"
        handle_error(error_msg)

# ----------------- 总调度器 -----------------
def master_job():
    print("\n" + "="*50)
    print_log("--- ibot 开始执行全量巡检 ---")
    
    try:
        fetch_sjtu_news()
        fetch_canvas_updates()
        
        print_log("--- ibot 巡检完毕，进入休眠 ---")
    except Exception as e:
        error_msg = f"总调度器异常: {e}"
        handle_error(error_msg)
    finally:
        print("="*50 + "\n")

# 每隔 30 分钟运行一次总任务 (而不是设定具体的小时)
schedule.every(30).minutes.do(master_job)

if __name__ == "__main__":
    print_log("ibot 定时服务启动，频率：每 30 分钟")
    
    # 启动时先立刻跑一次，确认所有接口都通了
    master_job()
    
    while True:
        schedule.run_pending()
        time.sleep(10)