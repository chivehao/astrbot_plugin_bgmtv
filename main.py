from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig

@register("bgmtv", "chivehao", "AstrBot 插件, 关于Bangumi 番组计划。", "1.0.0")
class BangumiTvPlugin(Star):
    access_token = ""
    user_agent = ""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        logger.info("开始初始化...")
        self.config = config
        self.access_token = self.config.get("access_token", "")
        self.user_agent = self.config.get("user_agent", "AstrBot-BGMTV-Plugin/2.0")
        self.config.save_config()
        logger.info("...已完成初始化。")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""


    @filter.command("条目查询")
    async def helloworld(self, event: AstrMessageEvent):
        """条目查询 {id}""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!") # 发送一条纯文本消息

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
