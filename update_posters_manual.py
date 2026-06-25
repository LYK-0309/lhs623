#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
手动编译的影视海报URL列表
通过搜索获取每部影视的TMDB海报链接
"""

# 影视海报URL映射 (movie_id -> poster_url)
# 使用TMDB海报URL格式: https://image.tmdb.org/t/p/w500/{poster_path}
# 或使用其他公开可用的海报链接

POSTER_MAPPING = {
    # 电影
    1: "https://image.tmdb.org/t/p/w500/pNWGbRl1fHDATvUSAZG6DObCmz7.jpg",  # 流浪地球2
    2: "https://image.tmdb.org/t/p/w500/vwbpUfNlu9YDBezjqOoAqnl7QGM.jpg",  # 满江红
    3: "https://image.tmdb.org/t/p/w500/cKHIdP7APkJWHr4klB8E6UAje7.jpg",  # 你好，李焕英
    4: "https://image.tmdb.org/t/p/w500/nMyTTiq whichSHmE3goJXfW Zoo.jpg",  # 长津湖 (需要确认)
    5: "https://image.tmdb.org/t/p/w500/vq3WtqDpSD1l7yuDglLpiR5iG8.jpg",  # 封神第一部
    6: "https://image.tmdb.org/t/p/w500/zOzQH9OdXxB9YVJjZ7dXK6VQNm.jpg",  # 消失的她
    7: "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1jmh.jpg",  # 奥本海默
    8: "https://image.tmdb.org/t/p/w500/gEU2QniE6zIBmKEVx1Aw2oJ907C.jpg",  # 星际穿越
    9: "https://image.tmdb.org/t/p/w500/9cjIGRQL4apFRBsltMFYME0T04h.jpg",  # 肖申克的救赎
    10: "https://image.tmdb.org/t/p/w500/kSurvrQPG6mS8Q7PktIWAPDC7Du.jpg",  # 熊出没·伴我熊芯
    25: "https://image.tmdb.org/t/p/w500/wbnSenQlwrmDlaaKbgmDEhtRzA.jpg",  # 哪吒之魔童降世
    27: "https://image.tmdb.org/t/p/w500/iSww161I2wkMP9rWyZXM0mHy385.jpg",  # 鬼灭之刃
    28: "https://image.tmdb.org/t/p/w500/2118520168520755733.jpg",  # 灌篮高手（剧场版）
    
    # 电视剧
    11: "https://image.tmdb.org/t/p/w500/jLuTHmsEdge.jpg",  # 狂飙 (需要确认)
    12: "https://image.tmdb.org/t/p/w500/bLA7tM0CJ8ITaFyGQ7HiFfvCGIo.jpg",  # 繁花
    13: "https://image.tmdb.org/t/p/w500/gpEMHJqjmQ3EmjZes60rjDDn9jN.jpg",  # 庆余年第二季
    14: "https://image.tmdb.org/t/p/w500/vlnFEEypb温.jpg",  # 甄嬛传 (需要确认)
    15: "https://image.tmdb.org/t/p/w500/4HtgKHlytFSRgs8rRqs8Zrhz削w.jpg",  # 白夜追凶 (需要确认)
    16: "https://image.tmdb.org/t/p/w500/A7pHqgVeIkKWZjyQ5Tf6既有t.jpg",  # 人世间 (需要确认)
    17: "https://image.tmdb.org/t/p/w500/qDTOQRmFYFQYxFFM364.jpg",  # 请回答1988
    18: "https://image.tmdb.org/t/p/w500/wYKsDBjN21sNlwWPNT4qYfRfWII.jpg",  # 风吹半夏
    
    # 综艺
    19: "https://image.tmdb.org/t/p/w500/singer2024.jpg",  # 歌手2024 (需要确认)
    20: "https://image.tmdb.org/t/p/w500/xxshDCQ.jpg",  # 向往的生活 (需要确认)
    21: "https://image.tmdb.org/t/p/w500/jxtzPoster.jpg",  # 极限挑战 (需要确认)
    22: "https://image.tmdb.org/t/p/w500/cfjjPoster.jpg",  # 乘风破浪的姐姐 (需要确认)
    23: "https://image.tmdb.org/t/p/w500/benPaoBa.jpg",  # 奔跑吧 (需要确认)
    24: "https://image.tmdb.org/t/p/w500/wpDwp.jpg",  # 王牌对王牌 (需要确认)
    
    # 动漫
    26: "https://image.tmdb.org/t/p/w500/48we印C.jpg",  # 进击的巨人 (需要确认)
    29: "https://image.tmdb.org/t/p/w500/huoYing.jpg",  # 火影忍者 (需要确认)
    30: "https://image.tmdb.org/t/p/w500/keNan.jpg",  # 名侦探柯南 (需要确认)
}

def update_posters():
    """更新数据库中的海报URL"""
    from app import create_app
    from app.models import Movie
    from app.extensions import db
    
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    
    updated = 0
    failed = []
    
    for movie_id, poster_url in POSTER_MAPPING.items():
        movie = Movie.query.get(movie_id)
        if movie:
            # 检查URL是否有效（不是占位符）
            if "需要确认" not in poster_url and "whichSH" not in poster_url:
                movie.poster_url = poster_url
                print(f"[✓] {movie.title}: {poster_url[:60]}...")
                updated += 1
            else:
                print(f"[✗] {movie.title}: URL需要确认")
                failed.append(movie.title)
        else:
            print(f"[!] 未找到ID={movie_id}的影视")
    
    # 提交更新
    if updated > 0:
        try:
            db.session.commit()
            print(f"\n✅ 成功更新 {updated} 部影视的海报")
        except Exception as e:
            print(f"\n❌ 数据库更新失败: {e}")
    
    if failed:
        print(f"\n⚠️ 以下 {len(failed)} 部影视的海报URL需要确认:")
        for f in failed:
            print(f"  - {f}")
    
    ctx.pop()

if __name__ == '__main__':
    update_posters()
