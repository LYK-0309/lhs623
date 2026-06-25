# -*- coding: utf-8 -*-
"""
自动搜索缺失预告片的 Bilibili BV 号
针对剩余14部没有预告片的影视
"""
import time
import requests
import sys

# 需要搜索的影视列表 (id, title, search_keywords)
MOVIES_TO_SEARCH = [
    (9, "肖申克的救赎", "肖申克的救赎 1994 预告片"),
    (10, "熊出没·伴我熊芯", "熊出没伴我熊芯 2023 电影预告"),
    (11, "狂飙", "狂飙 电视剧 2023 定档预告"),
    (14, "甄嬛传", "甄嬛传 电视剧 2011 开播宣传"),
    (15, "白夜追凶", "白夜追凶 电视剧 2017 预告"),
    (16, "人世间", "人世间 电视剧 2022 预告片"),
    (18, "风吹半夏", "风吹半夏 电视剧 2022 赵丽颖 预告"),
    (20, "向往的生活", "向往的生活 湖南卫视 综艺 预告"),
    (21, "极限挑战", "极限挑战 综艺 东方卫视 预告"),
    (22, "乘风破浪的姐姐", "乘风破浪的姐姐 芒果TV 综艺 预告"),
    (23, "奔跑吧", "奔跑吧 浙江卫视 综艺 跑男 预告"),
    (24, "王牌对王牌", "王牌对王牌 浙江卫视 综艺 预告"),
    (29, "火影忍者", "火影忍者 疾风传 开播宣传 中文"),
    (30, "名侦探柯南", "名侦探柯南 动画 开播宣传 中文"),
]

def search_bilibili_bv(title, keywords, max_retry=3):
    """通过 Bilibili 搜索 API 查找 BV 号"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com',
    }
    
    for attempt in range(max_retry):
        try:
            # 搜索视频
            api_url = 'https://api.bilibili.com/x/web-interface/search/type'
            params = {
                'search_type': 'video',
                'keyword': keywords,
                'order': 'click',  # 按点击量排序，更容易找到官方预告
                'duration': '1',    # 短时长（预告片通常较短）
                'page': 1,
            }
            
            resp = requests.get(api_url, params=params, headers=headers, timeout=15)
            data = resp.json()
            
            if data.get('code') == 0 and data.get('data', {}).get('result'):
                results = data['data']['result']
                # 过滤出可能是预告片的结果
                for r in results[:5]:
                    title_lower = r.get('title', '').lower()
                    # 检查标题是否包含"预告"、"宣传"、"定档"等关键词
                    if any(kw in title_lower for kw in ['预告', '宣传', '定档', '片花', '特辑', 'official', 'trailer']):
                        bvid = r.get('bvid')
                        title_found = r.get('title', '')
                        author = r.get('author', '')
                        play = r.get('play', 0)
                        print(f"    ✓ 找到: BV={bvid}, 标题={title_found}, UP主={author}, 播放={play}")
                        return bvid
                
                # 如果没有找到含"预告"的，返回第一个结果的 BV
                if results:
                    r = results[0]
                    bvid = r.get('bvid')
                    title_found = r.get('title', '')
                    author = r.get('author', '')
                    play = r.get('play', 0)
                    print(f"    △ 找到(无预告标签): BV={bvid}, 标题={title_found}, UP主={author}, 播放={play}")
                    return bvid
            
            elif data.get('code') == 412 or '412' in str(data):
                print(f"    ⚠ 请求被限流 (412)，等待 {10 + attempt * 5} 秒后重试...")
                time.sleep(10 + attempt * 5)
                continue
            
            else:
                print(f"    ✗ API 返回异常: {data.get('code')} - {data.get('message', '')}")
        
        except Exception as e:
            print(f"    ✗ 请求失败 (尝试 {attempt+1}/{max_retry}): {e}")
            if attempt < max_retry - 1:
                time.sleep(5)
    
    return None

def main():
    print("=" * 60)
    print("开始搜索缺失的 Bilibili 预告片 BV 号")
    print("=" * 60)
    
    results = []
    
    for movie_id, title, keywords in MOVIES_TO_SEARCH:
        print(f"\n[{movie_id}] {title}")
        print(f"  搜索关键词: {keywords}")
        
        bvid = search_bilibili_bv(title, keywords)
        
        if bvid:
            trailer_url = f'//player.bilibili.com/player.html?bvid={bvid}&page=1&autoplay=0&danmaku=0&high_quality=1'
            results.append((movie_id, title, trailer_url, bvid))
            print(f"  ✅ 已获取: {trailer_url}")
        else:
            print(f"  ❌ 未找到")
        
        # 每次搜索后等待，避免被限流
        time.sleep(3)
    
    print("\n" + "=" * 60)
    print(f"搜索完成！找到 {len(results)}/{len(MOVIES_TO_SEARCH)} 个预告片")
    print("=" * 60)
    
    if results:
        print("\nSQL 更新语句：")
        print("-" * 60)
        for movie_id, title, trailer_url, bvid in results:
            print(f"-- {title} (id={movie_id})")
            print(f"UPDATE movie SET trailer_url = '{trailer_url}' WHERE id = {movie_id};")
            print()
        
        # 同时输出 Python 更新代码
        print("\nPython 更新代码：")
        print("-" * 60)
        print("from app import create_app")
        print("from app.models import Movie")
        print("app = create_app()")
        print("ctx = app.app_context()")
        print("ctx.push()")
        for movie_id, title, trailer_url, bvid in results:
            print(f"Movie.query.get({movie_id}).trailer_url = '{trailer_url}'")
        print("db.session.commit()")
        print("ctx.pop()")
        print("-" * 60)

if __name__ == '__main__':
    main()
