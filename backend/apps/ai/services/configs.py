"""选择本次调用使用的 AI 模型配置。对话与账单解析共用。"""
from common.exceptions import BusinessError

from ..models import AIModelConfig


def resolve_ai_config(user, config_id=None, session_config_id=None) -> AIModelConfig:
    """
    优先级：显式指定 > 会话上记住的 > 默认配置 > 最近创建的。
    指定的配置不属于该用户时按"不存在"处理；完全没有配置时提示先配置。
    """
    configs = AIModelConfig.objects.filter(user=user)
    config = None
    if config_id:
        config = configs.filter(id=config_id).first()
        if config is None:
            raise BusinessError("AI 模型配置不存在", status=404)
    elif session_config_id:
        config = configs.filter(id=session_config_id).first()
    if config is None:
        # 没有默认配置时（比如默认的被删了）退而使用最近创建的，不让用户卡在"请先配置"
        config = configs.order_by("-is_default", "-id").first()
    if config is None:
        raise BusinessError("请先配置 AI 模型")
    return config
