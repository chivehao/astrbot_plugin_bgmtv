from typing import List
from pydantic import StrictStr
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig
import astrbot.api.message_components as Comp
import openapi_client
from openapi_client.rest import ApiException

configuration = openapi_client.Configuration(
    host = "https://api.bgm.tv"
)

@register("bgmtv", "chivehao", "AstrBot 插件, 关于Bangumi 番组计划。", "1.0.0")
class BangumiTvPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.config.save_config()

    @filter.command("条目查询")
    async def searchSubject(self, event: AstrMessageEvent):
        """条目查询 (动画/游戏/书籍/音乐/三次元) [关键词/ID]""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。

        user_name = event.get_sender_name()
        cmd = event.message_str.split(maxsplit=2)
        if len(cmd) < 2:
            return event.plain_result("格式错误，用法: /条目查询 (动画/游戏/书籍/音乐/三次元) [关键词/ID]")

        

        search_type = openapi_client.SubjectType.Anime

        if (len(cmd) == 2):
            query = cmd[1].strip()
        else:
            # 指定了查询的条目类型
            search_type = str2type(str=cmd[1].strip())
            query = cmd[2].strip()

        configuration = openapi_client.Configuration(access_token = self.config.get("access_token", ""))
        with openapi_client.ApiClient(configuration) as api_client:
            api_client.user_agent = self.config.get("user_agent", "AstrBot-BGMTV-Plugin/2.0")
            # logger.info(f"token:{configuration.access_token}\nuser-agent:{api_client.user_agent}")
            api_instance = openapi_client.DefaultApi(api_client)

            try:
                name, name_cn, summary, cover_url, var_date = "", "", "", "", ""
                type = openapi_client.SubjectType
                tags = []

                if query.isdigit():
                    subject_id = int(query) # int | 条目 ID
                    subject = api_instance.get_subject_by_id(subject_id)
                    name = subject.name
                    name_cn = subject.name_cn
                    summary = subject.summary
                    cover_url = subject.images.large
                    type = subject.type
                    var_date = subject.var_date
                    tags = [tag.name for tag in subject.tags]
                else:
                    # return event.plain_result("暂未支持关键词查询。")
                    limit = 1 # int | 分页参数 (optional)
                    search_subjects_request = openapi_client.SearchSubjectsRequest(keyword=query, sort="rank", filter=openapi_client.SearchSubjectsRequestFilter(type=[search_type]))
                    logger.info(f"search type: {search_type} keyword: {query}")
                    api_responses = api_instance.search_subjects(limit=limit, search_subjects_request=search_subjects_request)
                    if api_responses.total > 0 :
                        search_subject:openapi_client.SearchSubject = api_responses.data[0]
                        name = search_subject.name
                        name_cn = search_subject.name_cn
                        summary = search_subject.summary
                        cover_url = search_subject.image
                        type = search_subject.type
                        var_date = search_subject.var_date
                        tags = [tag.name for tag in search_subject.tags]
                
                if name == "":
                    return event.plain_result("未找到条目。")

                subject_result_card:bool = self.config.get("subject_result_card")
                
                if (subject_result_card) :
                    renderMap = {
                        "tags": tags, "name": name, 
                        "name_cn": name_cn,
                        "type": type2str(type=type),
                        "cover_url": cover_url,
                        "air_date": var_date,
                        "summary": summary
                    }
                    options = {
                        "full_page": True,
                        "omit_background": True,
                        "type": "jpeg",
                        "quality": 100
                    }
                    url = await self.html_render(TMPL, renderMap, options=options)
                    return event.image_result(url)  
                else:
                    chain = [
                        Comp.Plain(f"Hello, {user_name}, 你查询的结果如下："),
                        Comp.Plain(f"名称：{name}\n中文名：{name_cn}\n简介：{summary}\n封面："),
                        Comp.Image.fromURL(cover_url)
                    ]
                    return event.chain_result(chain)
            except Exception as e:
                logger.error("Exception when calling DefaultApi->get_subject_by_id: %s\n" % e)
                return event.chain_result("内部异常，请查看日志！！")


def type2str(type: openapi_client.SubjectType):
    if (type == 1): return "书籍"
    elif (type == 2): return "动画"
    elif (type == 3): return "音乐"
    elif (type == 4): return "游戏"
    elif (type == 6): return "三次元"
    else: return "未知"

def str2type(str) -> openapi_client.SubjectType:
    if ("动画" == str): return openapi_client.SubjectType.Anime
    elif ("书籍" == str): return openapi_client.SubjectType.Book
    elif ("音乐" == str): return openapi_client.SubjectType.Music
    elif ("游戏" == str): return openapi_client.SubjectType.Game
    elif ("三次元" == str): return openapi_client.SubjectType.Real
    else: return openapi_client.SubjectType.Anime



# 自定义的 Jinja2 模板，支持 CSS
TMPL = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
        }
        
        .entry-card {
            display: flex;
            width: 100%;
            max-width: 100%;
            background-color: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            height: 100%;
            position: relative;
        }
        
        .entry-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        }
        
        .cover-section {
            width: 40%;
            position: relative;
            overflow: visible;
        }
        
        .cover-image {
            width: 100%;
            height: auto; /* 关键：让高度随图片比例自适应 */
            object-fit: contain; /* 或 scale-down; 完整显示图片，不会裁剪 */
            display: block; /* 避免图片底部出现间隙 */
        }
        
        .entry-card:hover .cover-image {
            transform: scale(1.05);
        }
        
        .cover-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(to bottom, rgba(0,0,0,0) 70%, rgba(0,0,0,0.3) 100%);
        }
        
        .info-section {
            width: 60%;
            padding: 24px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        .title-row {
            margin-bottom: 15px;
        }
        
        .name-en {
            font-size: 2rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }
        
        .name-cn {
            font-size: 2rem;
            color: #083957;
            font-weight: 500;
            position: relative;
            display: inline-block;
            padding-bottom: 5px;
        }
        
        .name-cn::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 45px;
            height: 3px;
            background-color: #3cc2e7;
        }
        
        .description {
            color: #5d6d7e;
            line-height: 1.6;
            font-size: 1rem;
            flex-grow: 1;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 8;
            -webkit-box-orient: vertical;
        }
        
        .card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #f0f0f0;
        }
        
        .tags {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        
        .tag {
            background-color: #f0f8ff;
            color: #3498db;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        
        .card-badge {
            position: absolute;
            top: 15px;
            left: 15px;
            background-color: #3498db;
            color: white;
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            z-index: 2;
        }
        
        .release-date {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-top: 5px;
            display: flex;
            align-items: center;
        }

        .date-icon {
            margin-right: 6px;
            font-style: normal !important; 
            transform: rotate(0deg) !important;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="entry-card">
        <div class="cover-section">
            <div class="card-badge">{{type}}</div>
            <div class="cover-overlay"></div>
            <img class="cover-image" src="{{cover_url}}" alt="条目封面">
        </div>
        <div class="info-section">
            <div>
                <div class="title-row">
                    <div class="name-en">{{name}}</div>
                    <div class="name-cn">{{name_cn}}</div>
                    <div class="release-date">
                        <i class="date-icon">📅</i> {{air_date}}
                    </div>
                </div>
                <div class="description">{{summary}}</div>
            </div>
            <div class="card-footer">
                <div class="tags">
                    {% for tag in tags %}
                        <span class="tag">{{tag}}</span>
                    {% endfor %}
                </div>
            </div>
        </div>

        {% for item in items %}
            <li>{{ item }}</li>
        {% endfor %}
    </div>
</body>
</html>
'''