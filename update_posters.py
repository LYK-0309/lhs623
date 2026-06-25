# -*- coding: utf-8 -*-
"""
为所有影视更新真实海报图片
使用豆瓣电影 API 搜索海报
"""
import urllib.request
import urllib.parse
import json
import time
import re
import sys

# 所有影视列表 (id, title, search_keyword)
MOVIES = [
    (1, "流浪地球2", "流浪地球2 2023"),
    (2, "满江红", "满江红 2023 张艺谋"),
    (3, "你好，李焕英", "你好李焕英 2021"),
    (4, "长津湖", "长津湖 2021"),
    (5, "封神第一部：朝歌风云", "封神第一部 朝歌风云 2023"),
    (6, "消失的她", "消失的她 2023"),
    (7, "奥本海默", "奥本海默 2023"),
    (8, "星际穿越", "星际穿越 2014"),
    (9, "肖申克的救赎", "肖申克的救赎 1994"),
    (10, "熊出没·伴我熊芯", "熊出没伴我熊芯 2023"),
    (11, "狂飙", "狂飙 电视剧 2023"),
    (12, "繁花", "繁花 电视剧 2023"),
    (13, "庆余年 第二季", "庆余年第二季 2024"),
    (14, "甄嬛传", "甄嬛传 电视剧 2011"),
    (15, "白夜追凶", "白夜追凶 电视剧 2017"),
    (16, "人世间", "人世间 电视剧 2022"),
    (17, "请回答1988", "请回答1988 韩剧 2015"),
    (18, "风吹半夏", "风吹半夏 电视剧 2022"),
    (19, "歌手2024", "歌手2024 综艺"),
    (20, "向往的生活", "向往的生活 综艺"),
    (21, "极限挑战", "极限挑战 综艺"),
    (22, "乘风破浪的姐姐", "乘风破浪的姐姐 综艺"),
    (23, "奔跑吧", "奔跑吧 综艺"),
    (24, "王牌对王牌", "王牌对王牌 综艺"),
    (25, "哪吒之魔童降世", "哪吒之魔童降世 2019"),
    (26, "进击的巨人", "进击的巨人 动漫"),
    (27, "鬼灭之刃", "鬼灭之刃 动漫"),
    (28, "灌篮高手（剧场版）", "灌篮高手 剧场版 2022"),
    (29, "火影忍者", "火影忍者 动漫"),
    (30, "名侦探柯南", "名侦探柯南 动漫"),
]

def search_douban_poster(title, keyword):
    """
    搜索豆瓣获取海报URL
    返回海报图片的直接URL
    """
    # 方法1: 搜索豆瓣电影API
    try:
        # 豆瓣搜索API
        search_url = "https://movie.douban.com/j/subject_suggest?" + urllib.parse.urlencode({'q': keyword})
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://movie.douban.com/',
        }
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        if data and len(data) > 0:
            # 获取第一个搜索结果的ID
            subject_id = data[0].get('id', '')
            title_found = data[0].get('title', '')
            year = data[0].get('year', '')
            print(f"    豆瓣搜索: {title_found} ({year}), ID={subject_id}")
            
            if subject_id:
                # 获取电影详情页，提取海报URL
                subject_url = f"https://movie.douban.com/subject/{subject_id}/"
                return fetch_douban_poster(subject_url, title)
    except Exception as e:
        print(f"    豆瓣搜索失败: {e}")
    
    # 方法2: 尝试直接搜索海报图片
    return search_poster_image(title, keyword)

def fetch_douban_poster(subject_url, title):
    """从豆瓣电影页面提取海报图片URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://movie.douban.com/',
        }
        req = urllib.request.Request(subject_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')
        
        # 提取 og:image 元数据
        og_image = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if og_image:
            poster_url = og_image.group(1)
            print(f"    ✓ 找到海报: {poster_url}")
            return poster_url
        
        # 备用: 提取海报div中的图片
        poster_img = re.search(r'<div class="poster">\s*<a[^>]*>\s*<img[^>]*src="([^"]+)"', html)
        if poster_img:
            poster_url = poster_img.group(1)
            print(f"    ✓ 找到海报: {poster_url}")
            return poster_url
        
        print(f"    ✗ 未找到海报图片")
    except Exception as e:
        print(f"    ✗ 获取海报失败: {e}")
    
    return None

def search_poster_image(title, keyword):
    """搜索海报图片的直接URL（备用方法）"""
    try:
        # 搜索百度图片或其他图片源
        # 这里使用豆瓣的图片搜索作为备用
        search_url = "https://www.douban.com/search?" + urllib.parse.urlencode({'q': keyword + ' 海报'})
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.douban.com/',
        }
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
        
        # 提取图片URL
        img_urls = re.findall(r'https?://[^\s"\']+\.(?:jpg|jpeg|png|webp)[^\s"\']*', html)
        if img_urls:
            # 过滤出可能是海报的URL
            for url in img_urls[:5]:
                if 'douban' in url or 'poster' in url or 'img' in url:
                    print(f"    △ 找到图片(备用): {url}")
                    return url
    except Exception as e:
        print(f"    ✗ 备用搜索失败: {e}")
    
    return None

def main():
    print("=" * 70)
    print("开始搜索并更新所有影视的海报")
    print("=" * 70)
    
    results = []
    failed = []
    
    for movie_id, title, keyword in MOVIES:
        print(f"\n[{movie_id}] {title}")
        print(f"  搜索关键词: {keyword}")
        
        poster_url = search_douban_poster(title, keyword)
        
        if poster_url:
            results.append((movie_id, title, poster_url))
            print(f"  ✅ 已获取海报URL")
        else:
            failed.append((movie_id, title))
            print(f"  ❌ 未找到海报")
        
        # 每次请求后等待，避免被限流
        time.sleep(2)
    
    print("\n" + "=" * 70)
    print(f"搜索完成！找到 {len(results)}/{len(MOVIES)} 个海报")
    print("=" * 70)
    
    if results:
        print("\n更新数据库的 Python 代码：")
        print("-" * 70)
        print("from app import create_app")
        print("from app.models import Movie")
        print("from app.extensions import db")
        print("app = create_app()")
        print("ctx = app.app_context()")
        print("ctx.push()")
        for movie_id, title, poster_url in results:
            print(f"m = Movie.query.get({movie_id})")
            print(f"m.poster_url = '{poster_url}'")
            print(f"print('已更新: {title}')")
        print("db.session.commit()")
        print("ctx.pop()")
        print("-" * 70)
    
    if failed:
        print(f"\n未找到海报的影视 ({len(failed)} 个):")
        for movie_id, title in failed:
            print(f"  - [{movie_id}] {title}")

if __name__ == '__main__':
    main()
