#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import create_app
from app.models import Movie
from datetime import datetime

app = create_app()
ctx = app.app_context()
ctx.push()

movies = Movie.query.all()
print(f"总计: {len(movies)} 部影视")
print("=" * 100)

for m in movies:
    # 获取年份
    year = m.release_date.year if m.release_date else "未知"
    
    # 截断过长的URL用于显示
    poster_display = m.poster_url
    if poster_display and len(poster_display) > 80:
        poster_display = poster_display[:80] + "..."
    
    print(f"[{m.id}] {m.title} ({year})")
    print(f"    海报: {poster_display}")
    print("-" * 100)

ctx.pop()
