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
        """条目查询 [角色ID]""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。

        user_name = event.get_sender_name()
        cmd = event.message_str.split(maxsplit=1)
        if len(cmd) < 2:
            return event.plain_result("格式错误，用法: /条目查询 [角色ID]")

        query = cmd[1].strip()

        configuration = openapi_client.Configuration(access_token = self.config.get("access_token", ""))
        with openapi_client.ApiClient(configuration) as api_client:
            api_client.user_agent = self.config.get("user_agent", "AstrBot-BGMTV-Plugin/2.0")
            # logger.info(f"token:{configuration.access_token}\nuser-agent:{api_client.user_agent}")
            api_instance = openapi_client.DefaultApi(api_client)

            try:
                name, name_cn, summary, cover_url = "", "", "", ""

                if query.isdigit():
                    subject_id = int(query) # int | 条目 ID
                    subject = api_instance.get_subject_by_id(subject_id)
                    name = subject.name
                    name_cn = subject.name_cn
                    summary = subject.summary
                    cover_url = subject.images.large
                else:
                    # return event.plain_result("暂未支持关键词查询。")
                    limit = 1 # int | 分页参数 (optional)
                    offset = 5 # int | 分页参数 (optional)
                    search_subjects_request = openapi_client.SearchSubjectsRequest(keyword=query)
                    logger.info(f"search keyword: {query}")
                    api_responses = api_instance.search_subjects(limit=limit, offset=offset, search_subjects_request=search_subjects_request)
                    if api_responses.total > 0 :
                        search_subject:openapi_client.SearchSubject = api_responses.data[0]
                        name = search_subject.name
                        name_cn = search_subject.name_cn
                        summary = search_subject.summary
                        cover_url = search_subject.image
                
                if name == "":
                    return event.plain_result("未找到条目。")

                chain = [
                    Comp.Plain(f"Hello, {user_name}, 你查询的结果如下："),
                    Comp.Plain(f"名称：{name}\n中文名：{name_cn}\n简介：{summary}\n封面："),
                    Comp.Image.fromURL(cover_url)
                ]
                return event.chain_result(chain)
                # yield event.plain_result(f"Hello, {user_name}, 你查询的结果如下：\n {api_response}!")
            except Exception as e:
                logger.error("Exception when calling DefaultApi->get_subject_by_id: %s\n" % e)
                return event.chain_result("内部异常，请查看日志！！")

