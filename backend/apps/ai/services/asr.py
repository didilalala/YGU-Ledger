"""
语音识别。对应原项目 ai/services/asr.service.ts：
通过 OpenAI 兼容的 chat/completions 接口调用 qwen3-asr-flash，音频以 base64 input_audio 发送。
"""
import logging
import time

import httpx
from django.conf import settings

from common.exceptions import BusinessError

logger = logging.getLogger(__name__)


def transcribe(audio_base64: str, mime_type: str = "audio/mp4") -> str:
    if not settings.ASR_API_URL or not settings.ASR_API_KEY:
        raise BusinessError("ASR 服务未配置，请设置 ASR_API_URL 和 ASR_API_KEY", status=503)

    body = {
        "model": settings.ASR_MODEL,
        "messages": [{
            "role": "user",
            "content": [{"type": "input_audio",
                         "input_audio": {"data": f"data:{mime_type};base64,{audio_base64}"}}],
        }],
        "stream": False,
        "asr_options": {"language": "zh", "enable_itn": True},
    }
    start = time.monotonic()
    resp = httpx.post(settings.ASR_API_URL, json=body, timeout=60,
                      headers={"Authorization": f"Bearer {settings.ASR_API_KEY}"})
    cost = (time.monotonic() - start) * 1000
    if resp.status_code != 200:
        logger.error("ASR 失败 %s %.0fms %s", resp.status_code, cost, resp.text[:500])
        raise BusinessError("语音识别失败", status=502)

    text = resp.json()["choices"][0]["message"]["content"] or ""
    logger.info("ASR 完成 %.0fms，文本长度 %d", cost, len(text))
    return text.strip()
