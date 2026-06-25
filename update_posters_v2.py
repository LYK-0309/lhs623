# -*- coding: utf-8 -*-
"""
使用 TMDB API 获取电影海报
TMDB 提供免费 API，海报 URL 格式: https://image.tmdb.org/t/p/w500{poster_path}
"""
import urllib.request
import urllib.parse
import json
import time
import sys

# TMDB API 配置
TMDB_API_KEY = "9b1ebea84d4f4a98f8695f7a44e3b2a"  # 公开可用的 demo key
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# 所有影视列表 (id, title, year, media_type)
# media_type: movie 或 tv
MOVIES = [
    # 电影
    (1, "流浪地球2", 2023, "movie"),
    (2, "满江红", 2023, "movie"),
    (3, "你好，李焕英", 2021, "movie"),
    (4, "长津湖", 2021, "movie"),
    (5, "封神第一部：朝歌风云", 2023, "movie"),
    (6, "消失的她", 2023, "movie"),
    (7, "奥本海默", 2023, "movie"),
    (8, "星际穿越", 2014, "movie"),
    (9, "肖申克的救赎", 1994, "movie"),
    (10, "熊出没·伴我熊芯", 2023, "movie"),
    (25, "哪吒之魔童降世", 2019, "movie"),
    (28, "灌篮高手（剧场版）", 2022, "movie"),
    # 电视剧
    (11, "狂飙", 2023, "tv"),
    (12, "繁花", 2023, "tv"),
    (13, "庆余年 第二季", 2024, "tv"),
    (14, "甄嬛传", 2011, "tv"),
    (15, "白夜追凶", 2017, "tv"),
    (16, "人世间", 2022, "tv"),
    (17, "请回答1988", 2015, "tv"),
    (18, "风吹半夏", 2022, "tv"),
    (20, "向往的生活", 2017, "tv"),
    (21, "极限挑战", 2015, "tv"),
    (22, "乘风破浪的姐姐", 2020, "tv"),
    (23, "奔跑吧", 2015, "tv"),
    (24, "王牌对王牌", 2016, "tv"),
    # 动漫
    (26, "进击的巨人", 2013, "tv"),
    (27, "鬼灭之刃", 2019, "tv"),
    (29, "火影忍者", 2002, "tv"),
    (30, "名侦探柯南", 1996, "tv"),
    # 综艺
    (19, "歌手2024", 2024, "tv"),
]

def search_tmdb(title, year, media_type):
    """搜索 TMDB 获取海报路径"""
    try:
        # 搜索电影或电视剧
        if media_type == "movie":
            url = f"{TMDB_BASE_URL}/search/movie"
        else:
            url = f"{TMDB_BASE_URL}/search/tv"
        
        params = urllib.parse.urlencode({
            'api_key': TMDB_API_KEY,
            'query': title,
            'year': year,
            'language': 'zh-CN',
        })
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        req = urllib.request.Request(f"{url}?{params}", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        if data.get('results') and len(data['results']) > 0:
            result = data['results'][0]
            poster_path = result.get('poster_path')
            title_found = result.get('title') or result.get('name', '')
            print(f"    ✓ TMDB找到: {title_found} (poster_path={poster_path})")
            if poster_path:
                return IMAGE_BASE_URL + poster_path
        else:
            print(f"    ✗ TMDB未找到结果")
    except Exception as e:
        print(f"    ✗ TMDB搜索失败: {e}")
    
    return None

def get_chinese_poster_fallback(title, movie_id):
    """备用方法：使用中文电影数据库获取海报"""
    # 尝试从豆瓣获取（使用不同的方法）
    try:
        # 尝试直接构造豆瓣图片URL
        # 豆瓣图片URL格式: https://img1.doubanio.com/view/photo/l/public/p{photo_id}.webp
        # 但我们不知道 photo_id，所以尝试搜索
        search_url = "https://www.douban.com/search?" + urllib.parse.urlencode({'q': title + ' 海报'})
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.douban.com/',
        }
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
        
        # 提取图片URL
        import re
        img_urls = re.findall(r'https?://[^\s"\']+\.(?:jpg|jpeg|png|webp)[^\s"\']*', html)
        for url in img_urls:
            if 'douban' in url and ('poster' in url or 'img' in url):
                print(f"    △ 豆瓣找到: {url[:80]}")
                return url
    except Exception as e:
        print(f"    ✗ 备用方法失败: {e}")
    
    return None

def main():
    print("=" * 70)
    print("使用 TMDB API 获取影视海报")
    print("=" * 70)
    
    results = []
    failed = []
    
    for movie_id, title, year, media_type in MOVIES:
        print(f"\n[{movie_id}] {title} ({year})")
        
        poster_url = search_tmdb(title, year, media_type)
        
        if not poster_url:
            print(f"  尝试备用方法...")
            poster_url = get_chinese_poster_fallback(title, movie_id)
        
        if poster_url:
            results.append((movie_id, title, poster_url))
            print(f"  ✅ 已获取海报URL")
        else:
            failed.append((movie_id, title))
            print(f"  ❌ 未找到海报")
        
        time.sleep(0.5)  # TMDB 限速
    
    print("\n" + "=" * 70)
    print(f"搜索完成！找到 {len(results)}/{len(MOVIES)} 个海报")
    print("=" * 70)
    
    if results:
        print("\nSQL 更新语句：")
        print("-" * 70)
        for movie_id, title, poster_url in results:
            print(f"-- {title}")
            print(f"UPDATE movie SET poster_url = '{poster_url}' WHERE id = {movie_id};")
            print()
        
        print("\nPython 更新代码：")
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
