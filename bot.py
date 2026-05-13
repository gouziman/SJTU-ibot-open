import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import time  
import schedule
import os

SC_KEY = os.getenv('SC_KEY')

def fetch_sjtu_news():
    url = "https://www.sjtu.edu.cn/tg/index.html"
    headers = {
        "User-Gouziman": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.sjtu.edu.cn/"
    }


    max_attempts = 3  # 最多尝试3次
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        try:
            # 1. 网络请求
            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                response.encoding = 'utf-8'
            except RequestException as e:
                if attempt < max_attempts:
                    print(f"【网络层警告】: 尝试第 {attempt} 次失败，5秒后再次尝试... 详情: {e}")
                    time.sleep(5)  # 等待5秒
                    continue  # 跳过本次循环，进入下一次尝试
                else:
                    print(f"【网络层异常】: 已尝试 {max_attempts} 次，均失败。请检查网络连接。")
                    return 

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.select('li')
            if not news_items:
                news_items = soup.find_all('li', class_='item')

            if not news_items:
                if attempt < max_attempts:
                    print(f"【解析层警告】: 第 {attempt} 次未找到内容，可能是页面加载不全或选择器写错了，5秒后重试...")
                    time.sleep(5)
                    continue
                else:
                    print("【解析层异常】: 解析失败，请检查选择器。")
                    return

            # --- 如果走到这里，说明请求和解析都成功了，直接跳出重试循环 ---
            print(f"--- 成功获取数据，共有 {len(news_items)} 条通知 ---")
            break 

        except Exception as e:
            if attempt < max_attempts:
                print(f"【未知系统错误】: 尝试第 {attempt} 次失败，5秒后重试... 详情: {e}")
                time.sleep(5)
                continue
            else:
                print(f"【未知系统错误】: 已重试完毕，正在退出。。。")
                return

    try:
        try:
            with open("history.txt", "r", encoding="utf-8") as f:
                history_content = f.read()
        except FileNotFoundError:
            history_content = ""

        for item in news_items:
            try:
                a_tag = item.find('a')
                if a_tag is None: continue
                
                title = item.get_text(strip=True)
                link = a_tag.get('href', '')
                if not link.startswith('http'):
                    link = "https://www.sjtu.edu.cn" + link
                
                # 去重判断
                if title in history_content:
                    continue
                
                # --- 发现新通知，开始处理 ---
                print(f"发现新通知：{title}\n{link}")

                # 使用 Server酱推送
                push_url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
                push_data = {
                    "title": "【ibot】来自交大的新通知",
                    "desp": f"**通知标题：** {title}\n\n**详情链接：** [点击跳转]({link})"
                }

                # 发送请求给 Server酱
                try:
                    # 发送推送
                    push_res = requests.post(push_url, data=push_data, timeout=10)
                    if push_res.status_code == 200:
                        print(">>> 微信推送已发出")
                    else:
                        print(f">>> 推送失败，状态码: {push_res.status_code}")
                except Exception as push_err:
                    print(f">>> 推送接口报错: {push_err}")
                
                # 在推送后写入历史记录
                with open("history.txt", "a", encoding="utf-8") as f:
                    f.write(f"{title}\n{link}\n ----------------------------------------------------\n")
                    
            except Exception as e:
                print(f"【条目处理异常】: {e}")
                continue
                
    except Exception as e:
        print(f"【其它错误】: {e}")


schedule.every().day.at("08:00").do(fetch_sjtu_news)
schedule.every().day.at("12:00").do(fetch_sjtu_news)
schedule.every().day.at("23:30").do(fetch_sjtu_news)

print("ibot 已启动，正在后台守候...")
print("设定时间：08:00, 12:00, 22:00")

if __name__ == "__main__":
    fetch_sjtu_news()
    
    while True:
        schedule.run_pending()
        time.sleep(10)