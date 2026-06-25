"""
真实影视数据填充脚本
运行方式：python seed_movies.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, datetime
from app import create_app
from app.extensions import db
from app.models import Category, Movie, Comment

app = create_app()

# ──────────────────────────────────────────────
# 数据定义
# ──────────────────────────────────────────────

MOVIES_DATA = {
    "电影": [
        {
            "title": "流浪地球2",
            "intro": (
                "太阳即将毁灭，人类在地球表面建造了大量推进器，"
                "将地球推离太阳系，启程奔向遥远的比邻星。在这一宏大计划实施之前，"
                "一场关于人类命运的终极抉择正悄然上演。吴京、刘德华联袂出演，"
                "特效震撼，工业水准迈上新台阶，中国科幻的里程碑之作。"
            ),
            "actors": "吴京、刘德华、李雪健、沙溢、宁理",
            "release_date": date(2023, 1, 22),
            "rating": 8.3,
            "poster_url": "https://picsum.photos/seed/wlqq2/300/450",
        },
        {
            "title": "满江红",
            "intro": (
                "南宋绍兴年间，岳飞死后四年，秦桧率大队人马准备与金人会谈。"
                "一名小兵与神秘女子的相遇，引发了一场惊天谜局。"
                "张艺谋导演，悬疑与喜剧完美融合，沈腾、易烊千玺贡献精彩表演，"
                "结尾慷慨激昂令人动容。"
            ),
            "actors": "沈腾、易烊千玺、张译、雷佳音、岳云鹏",
            "release_date": date(2023, 1, 22),
            "rating": 8.0,
            "poster_url": "https://picsum.photos/seed/mjh/300/450",
        },
        {
            "title": "你好，李焕英",
            "intro": (
                "贾晓玲意外穿越到1981年，与年轻时的母亲李焕英成为好友。"
                "她试图改变母亲的命运，让她过上更幸福的生活，"
                "却在最后揭开了令人泪崩的真相。贾玲首部导演作品，"
                "票房破54亿，是中国影史最卖座的女导演电影。"
            ),
            "actors": "贾玲、张小斐、沈腾、陈赫、李焕英",
            "release_date": date(2021, 2, 12),
            "rating": 8.2,
            "poster_url": "https://picsum.photos/seed/lhying/300/450",
        },
        {
            "title": "长津湖",
            "intro": (
                "1950年，中国人民志愿军第九兵团奉命入朝参战。"
                "在极度严寒的长津湖战役中，志愿军战士以钢铁意志与美军展开殊死搏斗，"
                "创造了抗美援朝战争中最为惨烈的战役奇迹。"
                "吴京、易烊千玺主演，三位导演联合执导，史诗战争巨制。"
            ),
            "actors": "吴京、易烊千玺、朱亚文、李晨、胡军",
            "release_date": date(2021, 9, 30),
            "rating": 7.9,
            "poster_url": "https://picsum.photos/seed/cjh/300/450",
        },
        {
            "title": "封神第一部：朝歌风云",
            "intro": (
                "商王殷寿勾连狐妖妲己，暴虐无道；"
                "西伯侯之子姬发受命于天，踏上斩神封神之路。"
                "乌尔善导演历时8年打造的奇幻史诗，视觉震撼，"
                "费翔饰演的殷寿惊艳全场，中国神话世界观构建宏大。"
            ),
            "actors": "费翔、于适、妮露、李雪健、黄渤",
            "release_date": date(2023, 7, 20),
            "rating": 7.8,
            "poster_url": "https://picsum.photos/seed/fsgod/300/450",
        },
        {
            "title": "消失的她",
            "intro": (
                "何非在海岛旅游途中声称妻子李木子失踪，警察介入调查，"
                "一个女性深陷婚姻谎局的惊天秘密逐渐浮出水面。"
                "朱一龙、倪妮主演，改编自苏联电影《镜中人》，"
                "悬疑反转不断，引发广泛社会讨论。"
            ),
            "actors": "朱一龙、倪妮、文咏珊、李现",
            "release_date": date(2023, 6, 22),
            "rating": 7.0,
            "poster_url": "https://picsum.photos/seed/xsdt/300/450",
        },
        {
            "title": "奥本海默",
            "intro": (
                "原子弹之父J·罗伯特·奥本海默在二战期间主导【曼哈顿计划】，"
                "研发出改变世界格局的核武器，却在战后因政治迫害而遭受审判。"
                "克里斯托弗·诺兰导演，基里安·墨菲奉献生涯最佳演出，"
                "荣获第96届奥斯卡最佳影片等七项大奖。"
            ),
            "actors": "基里安·墨菲、艾米莉·布朗特、马特·达蒙、小罗伯特·唐尼",
            "release_date": date(2023, 8, 30),
            "rating": 8.9,
            "poster_url": "https://picsum.photos/seed/oppenheimer/300/450",
        },
        {
            "title": "星际穿越",
            "intro": (
                "地球面临粮食危机，前宇航员库珀受命穿越虫洞，"
                "前往另一个星系寻找人类新家园。在宇宙深处，时间以不同速度流逝，"
                "父女之间跨越时空的羁绊令人动容。诺兰执导的科幻神作，"
                "迄今为止最震撼的太空视觉体验之一。"
            ),
            "actors": "马修·麦康纳、安妮·海瑟薇、杰西卡·查斯坦、迈克尔·凯恩",
            "release_date": date(2014, 11, 12),
            "rating": 9.3,
            "poster_url": "https://picsum.photos/seed/interstellar/300/450",
        },
        {
            "title": "肖申克的救赎",
            "intro": (
                "银行家安迪·杜弗雷因被误判谋杀妻子及其情人入狱，"
                "在肖申克监狱结识了囚犯瑞德，两人建立了深厚友谊。"
                "安迪用近二十年时间实现了一个关于自由的伟大逃脱计划。"
                "豆瓣电影Top1，人类电影史上最伟大的作品之一。"
            ),
            "actors": "蒂姆·罗宾斯、摩根·弗里曼",
            "release_date": date(1994, 9, 23),
            "rating": 9.7,
            "poster_url": "https://picsum.photos/seed/shawshank/300/450",
        },
        {
            "title": "熊出没·伴我熊芯",
            "intro": (
                "光头强为了拯救患病的熊大，踏上了寻找【熊芯】的冒险旅程。"
                "然而旅途中他们发现了一个惊天秘密——一切的背后，"
                "都指向一段尘封已久的记忆。年度最催泪合家欢动画电影，"
                "让无数成年人在影院泪目。"
            ),
            "actors": "配音：张伟、潘霜霜、辛鹏",
            "release_date": date(2023, 1, 22),
            "rating": 8.0,
            "poster_url": "https://picsum.photos/seed/bear/300/450",
        },
    ],

    "电视剧": [
        {
            "title": "狂飙",
            "intro": (
                "1990年代至2021年，警察安欣与绰号黑老大的高启强三十年的命运纠葛。"
                "从弱小鱼贩到一方枭雄，高启强走过了一条无法回头的罪恶之路。"
                "张译、张颂文双雄对决，张颂文的表演令人叹服，"
                "成为2023年现象级国剧。"
            ),
            "actors": "张译、张颂文、李一桐、倪大红、韩童生",
            "release_date": date(2023, 1, 14),
            "rating": 9.0,
            "poster_url": "https://picsum.photos/seed/kuangbiao/300/450",
        },
        {
            "title": "繁花",
            "intro": (
                "1990年代的上海，阿宝、沪生、小毛三个年轻人在时代浪潮中"
                "追逐梦想、经历爱情与友情的跌宕起伏。"
                "王家卫首部电视剧作品，胡歌、唐嫣等强阵容，"
                "唯美影像风格令人沉醉，展现魔都旧日繁华。"
            ),
            "actors": "胡歌、唐嫣、马伊琍、辛芷蕾、游本昌",
            "release_date": date(2023, 12, 27),
            "rating": 8.0,
            "poster_url": "https://picsum.photos/seed/fanhua/300/450",
        },
        {
            "title": "庆余年 第二季",
            "intro": (
                "范闲在庆国朝堂上历经重重险阻，与太子、二皇子斗智斗勇，"
                "逐渐揭开母亲叶轻眉的身世之谜与庆帝的惊天秘密。"
                "时隔五年续集回归，张若昀、李沁再度出演，"
                "王启年、范思辙等配角依旧抢眼。"
            ),
            "actors": "张若昀、李沁、陈道明、吴刚、田雨",
            "release_date": date(2024, 5, 16),
            "rating": 8.3,
            "poster_url": "https://picsum.photos/seed/qynian2/300/450",
        },
        {
            "title": "甄嬛传",
            "intro": (
                "雍正年间，少女甄嬛因貌美入选后宫，从天真懵懂逐渐成长"
                "为深谙宫廷权谋的熹贵妃，一生都在权力与情感的漩涡中挣扎。"
                "孙俪奉献教科书级表演，台词精彩，人物塑造层次丰富，"
                "被誉为中国宫廷剧巅峰之作，全球累计播放量超百亿。"
            ),
            "actors": "孙俪、陈建斌、蔡少芬、刘雪华、斓曦",
            "release_date": date(2011, 11, 17),
            "rating": 9.4,
            "poster_url": "https://picsum.photos/seed/zhenhuanzhuan/300/450",
        },
        {
            "title": "白夜追凶",
            "intro": (
                "刑警队长关宏峰与弟弟关宏宇，一个只能在白天行动，"
                "一个只能在夜晚出没，两兄弟联手追查连环杀人案，"
                "同时试图证明弟弟的清白。潘粤明一人分饰两角，"
                "被誉为中国悬疑推理网剧的天花板，公安部推荐优秀作品。"
            ),
            "actors": "潘粤明、王龙正、陈创、林嘉欣",
            "release_date": date(2017, 8, 1),
            "rating": 9.0,
            "poster_url": "https://picsum.photos/seed/baiyzq/300/450",
        },
        {
            "title": "人世间",
            "intro": (
                "从1969年至今，跨越五十年，吉春市光字片胡同里，"
                "普通工人家庭周氏三兄妹各自坎坷又充实的人生故事。"
                "雷佳音、辛柏青、宋佳、殷桃主演，改编自茅盾文学奖同名小说，"
                "展现中国社会五十年变迁，感动无数观众。"
            ),
            "actors": "雷佳音、辛柏青、宋佳、殷桃、丁勇岱",
            "release_date": date(2022, 1, 28),
            "rating": 8.8,
            "poster_url": "https://picsum.photos/seed/renshijian/300/450",
        },
        {
            "title": "请回答1988",
            "intro": (
                "1988年首尔双门洞胡同里，五个相邻家庭的孩子们一起长大，"
                "经历爱情、友谊、告别与成长。温暖治愈的生活流叙事，"
                "引发几代观众的青春共鸣。豆瓣9.7分，"
                "被誉为韩剧史上最伟大的作品。"
            ),
            "actors": "李惠利、朴宝剑、柳俊烈、高庚杓、崔成元",
            "release_date": date(2015, 11, 6),
            "rating": 9.7,
            "poster_url": "https://picsum.photos/seed/reply1988/300/450",
        },
        {
            "title": "风吹半夏",
            "intro": (
                "1990年代，许半夏凭借机敏与胆识从废品收购起步，"
                "在废钢行业一路打拼成为商界女强人。"
                "赵丽颖、欧阳智薛主演，展现时代浪潮中女性的成长与蜕变，"
                "商战情节紧凑，人物弧光完整动人。"
            ),
            "actors": "赵丽颖、欧阳智薛、李光洁",
            "release_date": date(2022, 11, 28),
            "rating": 8.4,
            "poster_url": "https://picsum.photos/seed/fengbx/300/450",
        },
    ],

    "综艺": [
        {
            "title": "歌手2024",
            "intro": (
                "湖南卫视王牌音乐竞演节目回归，那英领衔中国歌手出战，"
                "与来自海外的顶尖歌手同台竞技。节目以直播形式播出，"
                "那英与KZ Tandingan等人的对决引发全网热议，"
                "\"中国人不是随随便便的\"成为年度名言。"
            ),
            "actors": "那英、汪苏泷、法老、海来阿木",
            "release_date": date(2024, 5, 10),
            "rating": 7.8,
            "poster_url": "https://picsum.photos/seed/singer2024/300/450",
        },
        {
            "title": "向往的生活",
            "intro": (
                "何炅、黄磊、彭昱畅在远离城市喧嚣的蘑菇屋，"
                "过一段慢节奏的田园生活。邀请嘉宾前来做客，"
                "一起种菜、做饭、聊天。最治愈的慢综艺，"
                "让人在快节奏的生活中感受到宁静与温暖。"
            ),
            "actors": "何炅、黄磊、彭昱畅、张子枫",
            "release_date": date(2017, 5, 12),
            "rating": 8.6,
            "poster_url": "https://picsum.photos/seed/xiangshenghuo/300/450",
        },
        {
            "title": "极限挑战",
            "intro": (
                "孙红雷、黄渤、罗志祥、王迅、张艺兴、黄磊六位男演员，"
                "化身极限男人帮，在全国各地接受各种极限挑战任务。"
                "每期节目暗藏社会议题，笑中有泪，"
                "曾被誉为综艺天花板，引发强烈共情。"
            ),
            "actors": "孙红雷、黄渤、罗志祥、王迅、张艺兴、黄磊",
            "release_date": date(2015, 6, 14),
            "rating": 9.0,
            "poster_url": "https://picsum.photos/seed/jixiantiaozhan/300/450",
        },
        {
            "title": "乘风破浪的姐姐",
            "intro": (
                "30位平均年龄30+的女星，重新登上舞台，展现女性力量与魅力。"
                "宁静一句\"你们不要惹我\"出圈，张雨绮、万茜等各展风采。"
                "节目引发社会对女性年龄与价值的广泛讨论，"
                "成为破圈的现象级综艺。"
            ),
            "actors": "宁静、张雨绮、万茜、郁可唯、伊能静",
            "release_date": date(2020, 6, 12),
            "rating": 8.0,
            "poster_url": "https://picsum.photos/seed/cfjj/300/450",
        },
        {
            "title": "奔跑吧",
            "intro": (
                "改编自韩国综艺《Running Man》的户外竞技真人秀，"
                "邓超、李晨、陈赫、Angelababy等人每期接受各种趣味挑战。"
                "搞笑与真情并存，多个经典名场面深入人心，"
                "是中国综艺史上长寿的常青树节目之一。"
            ),
            "actors": "邓超、李晨、陈赫、郑恺、迪丽热巴",
            "release_date": date(2014, 10, 10),
            "rating": 7.5,
            "poster_url": "https://picsum.photos/seed/runningman/300/450",
        },
        {
            "title": "王牌对王牌",
            "intro": (
                "沈腾、贾玲、华晨宇、关晓彤四位固定嘉宾，"
                "每期邀请不同主题的嘉宾团进行各种趣味竞技。"
                "沈腾与贾玲的搭档堪称综艺史上最强喜剧cp，"
                "每期节目都能带来意想不到的爆笑时刻。"
            ),
            "actors": "沈腾、贾玲、华晨宇、关晓彤",
            "release_date": date(2016, 2, 14),
            "rating": 8.2,
            "poster_url": "https://picsum.photos/seed/wangpai/300/450",
        },
    ],

    "动漫": [
        {
            "title": "哪吒之魔童降世",
            "intro": (
                "天地灵气孕育出一颗混元珠，元始天尊将其分为灵珠和魔丸。"
                "阴差阳错，本该是灵珠转世的哪吒，却成了魔丸降生。"
                "\"我命由我不由天\"——这个生来被众人嫌弃的孩子，"
                "用行动证明了命运由自己掌握。国漫里程碑，票房破50亿。"
            ),
            "actors": "配音：吕艳婷、囧森瑟夫、唐小喜",
            "release_date": date(2019, 7, 26),
            "rating": 9.0,
            "poster_url": "https://picsum.photos/seed/nezha/300/450",
        },
        {
            "title": "进击的巨人",
            "intro": (
                "人类被迫居住在高墙之内，以抵挡巨人的侵食。"
                "少年艾伦·耶格尔目睹母亲被巨人吞噬，"
                "发誓要消灭世上所有的巨人。随着秘密逐渐揭开，"
                "真正的敌人远比巨人更为复杂。被誉为神作的史诗级动漫。"
            ),
            "actors": "配音：梶裕贵、石川由依、井上麻里奈",
            "release_date": date(2013, 4, 7),
            "rating": 9.6,
            "poster_url": "https://picsum.photos/seed/aot/300/450",
        },
        {
            "title": "鬼灭之刃",
            "intro": (
                "大正时代，炭治郎的家人惨遭鬼灭，妹妹禰豆子变成了鬼。"
                "为了让妹妹变回人类，炭治郎加入鬼杀队，踏上了斩鬼之路。"
                "「无限列车篇」打破日本票房纪录，"
                "\"煉獄杏寿郎\"成为动漫史上最深入人心的角色之一。"
            ),
            "actors": "配音：花江夏树、鬼头明里、下野纮",
            "release_date": date(2019, 4, 6),
            "rating": 8.9,
            "poster_url": "https://picsum.photos/seed/kimetsu/300/450",
        },
        {
            "title": "灌篮高手（剧场版）",
            "intro": (
                "以流川枫、樱木花道、赤木刚宪等人为主角的青春热血高中篮球故事，"
                "2022年剧场版将目光聚焦在宫城良田身上，"
                "描述他与哥哥之间的羁绊与热爱篮球的初心。"
                "井上雄彦亲自执导，令一代人的青春记忆再度燃烧。"
            ),
            "actors": "配音：仲村宗悟、神尾晋一郎、三宅健太",
            "release_date": date(2022, 11, 4),
            "rating": 9.0,
            "poster_url": "https://picsum.photos/seed/slamdunk/300/450",
        },
        {
            "title": "火影忍者",
            "intro": (
                "体内封印着九尾妖狐的少年漩涡鸣人，从被全村嫌弃的孤独少年，"
                "一步一步成长为守护整个忍界的英雄。"
                "友情、梦想、牺牲……每一个经典场景都让无数人热泪盈眶。"
                "影响了一整代动漫迷的青春，影分身之术无人不知。"
            ),
            "actors": "配音：竹内顺子、井上和彦、中村千绘",
            "release_date": date(2002, 10, 3),
            "rating": 9.0,
            "poster_url": "https://picsum.photos/seed/naruto/300/450",
        },
        {
            "title": "名侦探柯南",
            "intro": (
                "高中生侦探工藤新一被黑衣组织灌下毒药后，"
                "身体缩小变成小学生，化名江户川柯南，"
                "隐藏在小兰身边继续追查组织踪迹。"
                "每年一部剧场版，始终保持高水准，"
                "是日本国民级推理动漫，也是童年的共同记忆。"
            ),
            "actors": "配音：高山南、山崎和佳奈、神谷明",
            "release_date": date(1996, 1, 8),
            "rating": 9.1,
            "poster_url": "https://picsum.photos/seed/conan/300/450",
        },
    ],
}


# ──────────────────────────────────────────────
# 示例影评数据
# ──────────────────────────────────────────────

SAMPLE_COMMENTS = {
    "流浪地球2": [
        {"author": "星河旅者", "content": "工业光魔水准！中国科幻终于站上世界舞台，MOSS那句让文明延续太震撼了。"},
        {"author": "宇宙漫游", "content": "刘德华的角色太催泪了，为了让女儿活着付出了一切，这才叫真正的父爱。"},
        {"author": "科幻迷小张", "content": "特效无可挑剔，故事比第一部更宏大，强烈推荐！"},
    ],
    "肖申克的救赎": [
        {"author": "电影发烧友", "content": "第一次看哭了，第二次看又哭了。希望是一件好事，也许是最好的事，好事从不消逝。"},
        {"author": "影痴老王", "content": "摩根·弗里曼的旁白简直是天籁，这辈子必看的电影。"},
        {"author": "豆瓣用户", "content": "改变了我的人生观，越是绝境越要保有希望。"},
    ],
    "狂飙": [
        {"author": "剧迷小美", "content": "张颂文的表演太厉害了，把高启强从鱼贩变成枭雄的过程演得丝丝入扣。"},
        {"author": "夜读书生", "content": "我读了那么多书，最后用来抄名单——这句话太心酸了。"},
        {"author": "追剧达人", "content": "连续三天熬夜看完，值了！安欣和高启强的命运纠葛太复杂太精彩。"},
    ],
    "甄嬛传": [
        {"author": "宫斗专家", "content": "真正的神作！每看一遍都有新发现，孙俪的表演无懈可击。"},
        {"author": "历史爱好者", "content": "台词太精彩，贱妾处世如履薄冰，随便拎一句都是人生哲理。"},
    ],
    "哪吒之魔童降世": [
        {"author": "国漫崛起", "content": "终于等到了可以和好莱坞动画分庭抗礼的国产作品！泪目。"},
        {"author": "小朋友家长", "content": "带孩子看了两遍，大人比孩子哭得更凶，我命由我不由天！"},
        {"author": "动漫fan", "content": "太乙真人骑着猪猪飞船太可爱了哈哈，笑中带泪的好故事。"},
    ],
    "进击的巨人": [
        {"author": "二次元大佬", "content": "神作无疑！每一季都在颠覆你的认知，剧情深度堪比文学作品。"},
        {"author": "巨人党", "content": "阿尔敏说过：放弃了什么都做不了，正因为什么都不放弃，才能做到。"},
    ],
    "星际穿越": [
        {"author": "物理系学生", "content": "诺兰对相对论的视觉化处理太绝了，和基普·索恩合作确保了科学严谨性。"},
        {"author": "感动一整年", "content": "父女之间跨越时间的爱，让我在影院嚎啕大哭，是我看过最动人的科幻片。"},
    ],
    "向往的生活": [
        {"author": "疲惫打工人", "content": "每次上班累了就来看这个，黄磊做饭的画面真的太治愈了。"},
        {"author": "田园梦想家", "content": "这就是我理想中的生活！离开城市，种菜，做饭，等朋友来。"},
    ],
}


# ──────────────────────────────────────────────
# 执行填充
# ──────────────────────────────────────────────

def seed():
    with app.app_context():
        if Movie.query.count() > 0:
            print("[!] 数据库中已存在影视数据，跳过填充。")
            print(f"    当前影视数：{Movie.query.count()} 部")
            print("    如需重新填充，请先删除 movie_review.db 文件后再运行。")
            return

        print("[*] 开始填充真实影视数据...\n")
        added_movies = {}

        for cat_name, movies in MOVIES_DATA.items():
            cat = Category.query.filter_by(name=cat_name).first()
            if not cat:
                cat = Category(name=cat_name)
                db.session.add(cat)
                db.session.flush()

            print(f"[+] 分类：{cat_name}")
            for m_data in movies:
                movie = Movie(
                    title=m_data["title"],
                    intro=m_data["intro"],
                    actors=m_data["actors"],
                    release_date=m_data["release_date"],
                    rating=m_data["rating"],
                    poster_url=m_data.get("poster_url"),
                    category_id=cat.id,
                )
                db.session.add(movie)
                db.session.flush()
                added_movies[m_data["title"]] = movie
                print(f"    OK  {m_data['title']} ({m_data['rating']}分)")

        # 添加示例影评
        print("\n[*] 添加示例影评...")
        total_comments = 0
        for title, comments in SAMPLE_COMMENTS.items():
            movie = added_movies.get(title)
            if movie:
                for c_data in comments:
                    comment = Comment(
                        content=c_data["content"],
                        author=c_data["author"],
                        movie_id=movie.id,
                    )
                    db.session.add(comment)
                    total_comments += 1

        db.session.commit()

        total = Movie.query.count()
        print(f"\n[OK] 填充完成！共添加 {total} 部影视、{total_comments} 条影评。")
        print("\n[*] 各分类统计：")
        for cat in Category.query.all():
            count = cat.movies.count()
            if count > 0:
                print(f"    {cat.name}：{count} 部")


if __name__ == "__main__":
    seed()
