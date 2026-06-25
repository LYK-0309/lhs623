#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 TMDB API 获取影视海报并更新数据库
TMDB API 文档: https://developer.themoviedb.org/reference/intro
"""

import urllib.request
import urllib.parse
import json
import time

# TMDB API 配置
# 使用演示 API key（公开可用，有频率限制）
TMDB_API_KEY = "9b1ebea84d4f4a98f8695f7a44e3b2a"  # 公开演示key
TMDB_BASE_URL = "https://api.themoviedb.org/3"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"

def search_movie(title, year=None):
    """搜索电影"""
    try:
        params = {
            'api_key': TMDB_API_KEY,
            'query': title,
            'language': 'zh-CN'
        }
        if year:
            params['year'] = year
        
        url = f"{TMDB_BASE_URL}/search/movie?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))
        
        if data.get('results') and len(data['results']) > 0:
            movie = data['results'][0]
            poster_path = movie.get('poster_path')
            if poster_path:
                return POSTER_BASE_URL + poster_path
        return None
    except Exception as e:
        print(f"    搜索电影失败: {e}")
        return None

def search_tv(title, first_air_date_year=None):
    """搜索电视剧"""
    try:
        params = {
            'api_key': TMDB_API_KEY,
            'query': title,
            'language': 'zh-CN'
        }
        if first_air_date_year:
            params['first_air_date_year'] = first_air_date_year
        
        url = f"{TMDB_BASE_URL}/search/tv?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))
        
        if data.get('results') and len(data['results']) > 0:
            tv = data['results'][0]
            poster_path = tv.get('poster_path')
            if poster_path:
                return POSTER_BASE_URL + poster_path
        return None
    except Exception as e:
        print(f"    搜索电视剧失败: {e}")
        return None

def main():
    from app import create_app
    from app.models import Movie
    
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    
    movies = Movie.query.all()
    print(f"开始为 {len(movies)} 部影视获取海报...")
    print("=" * 100)
    
    updated = 0
    failed = []
    
    for m in movies:
        title = m.title
        year = m.release_date.year if m.release_date else None
        
        print(f"[{m.id}] {title} ({year})")
        
        # 判断是电影还是电视剧（根据分类名称或标题关键词）
        # 获取分类名称
        category_name = m.category.name if m.category else ""
        
        poster_url = None
        
        # 尝试作为电影搜索
        print(f"    正在搜索...", end="")
        poster_url = search_movie(title, year)
        
        # 如果没找到，等待一下再试
        if not poster_url:
            time.sleep(0.5)
            # 尝试作为电视剧搜索
            poster_url = search_tv(title, year)
        
        if poster_url:
            m.poster_url = poster_url
            print(f" ✓ 成功")
            print(f"    海报: {poster_url}")
            updated += 1
        else:
            print(f" ✗ 未找到")
            failed.append(title)
        
        print("-" * 100)
        
        # 避免 API 限流
        time.sleep(0.3)
    
    # 提交数据库更新
    if updated > 0:
        try:
            from app.extensions import db
            db.session.commit()
            print(f"\n✅ 成功更新 {updated} 部影视的海报")
        except Exception as e:
            print(f"\n❌ 数据库更新失败: {e}")
    
    if failed:
        print(f"\n⚠️ 以下 {len(failed)} 部影视未找到海报:")
        for f in failed:
            print(f"  - {f}")
    
    ctx.pop()

if __name__ == '__main__':
    main()
