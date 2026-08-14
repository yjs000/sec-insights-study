"""
공용 LLM/임베딩 프로바이더 스위치.

study/.env의 LLM_PROVIDER 값으로 openai <-> nvidia(NIM, 무료)를 전환합니다.
Stage 5~9는 OpenAI(유료)를 직접 쓰는 대신 이 모듈의 get_llm()/get_embed_model()을
불러서 씁니다 — 한 곳만 바꾸면 모든 스테이지가 같이 바뀝니다.

NVIDIA NIM(build.nvidia.com)은 계정당 매달 무료 크레딧을 제공합니다. API 키는
https://build.nvidia.com 에서 모델 하나를 선택하고 "Get API Key"로 발급받습니다.

사용법 (study/.env):
    LLM_PROVIDER=nvidia
    NVIDIA_API_KEY=nvapi-...
또는:
    LLM_PROVIDER=openai   (기본값)
    OPENAI_API_KEY=sk-...
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()

# Nemotron 3 Ultra(550B, 2026-06 공개)는 build.nvidia.com NIM으로 무료 제공되는
# 모델 중 가장 크고 tool calling을 지원하는 모델입니다. 더 가벼운/빠른 모델이
# 필요하면 study/.env에서 NVIDIA_LLM_MODEL을 다른 값으로 override 하세요.
DEFAULT_NVIDIA_LLM_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
# "NV-Embed-QA"는 카탈로그엔 나오지만 레거시 "function" 엔드포인트로 라우팅되어
# 신규 발급 키에서는 404(Function ... Not found for account)가 나는 걸 직접 확인했습니다.
# 최신 NIM 카탈로그의 nv-embedqa-e5-v5로 대체합니다.
DEFAULT_NVIDIA_EMBED_MODEL = "nvidia/nv-embedqa-e5-v5"
DEFAULT_OPENAI_LLM_MODEL = "gpt-4o-mini"

# NVIDIA 임베딩 API는 512토큰이 하드 리밋입니다. 그런데 LlamaIndex의 SentenceSplitter는
# 청크 크기를 tiktoken(cl100k_base, GPT 계열 BPE)으로 재는 반면, NVIDIA 서버는 그 임베딩
# 모델 자신의(BERT/E5 계열) 토크나이저로 다시 셉니다. 두 토크나이저의 토큰 수가 달라서
# tiktoken 기준 500토큰짜리 청크가 NVIDIA 기준으로는 576토큰이 되어 400 에러가 나는 걸
# 직접 재현·확인했습니다 (576/463 ≈ 1.24배). 이 배율에 안전 마진을 더해 380으로 낮춥니다.
CHUNK_SIZE = 380 if PROVIDER == "nvidia" else 512
CHUNK_OVERLAP = 10


def get_llm(**overrides):
    """Settings.llm에 넣을 LLM 인스턴스. 두 프로바이더 모두 함수 호출(tool calling)을 지원합니다."""
    if PROVIDER == "nvidia":
        from llama_index.llms.nvidia import NVIDIA

        api_key = os.environ.get("NVIDIA_API_KEY")
        assert api_key, "study/.env에 NVIDIA_API_KEY를 채워주세요 (https://build.nvidia.com)"
        model = os.environ.get("NVIDIA_LLM_MODEL", DEFAULT_NVIDIA_LLM_MODEL)
        # NVIDIA 클래스는 카탈로그에서 이 모델의 "타입"(chat/completion, function calling
        # 지원 여부)을 자동으로 못 읽어와서 is_chat_model/is_function_calling_model이
        # 기본값 False로 잡힙니다. False로 두면 LLMQuestionGenerator 같은 코드가
        # llm.predict()를 호출할 때 (chat이 아니라) 구식 /v1/completions 엔드포인트로
        # 빠지는데, NVIDIA NIM은 이걸 지원하지 않아서 404가 납니다 — 직접 재현·확인함.
        # Nemotron 3 Ultra는 실제로 chat + tool calling을 지원하는 모델이므로 명시적으로 True를 줍니다.
        overrides.setdefault("is_chat_model", True)
        overrides.setdefault("is_function_calling_model", True)
        return NVIDIA(model=model, api_key=api_key, **overrides)
    else:
        from llama_index.llms.openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        assert api_key, "study/.env에 OPENAI_API_KEY를 채워주세요"
        model = os.environ.get("OPENAI_CHAT_MODEL", DEFAULT_OPENAI_LLM_MODEL)
        return OpenAI(model=model, api_key=api_key, temperature=0, **overrides)


def get_embed_model():
    """Settings.embed_model에 넣을 임베딩 모델 인스턴스."""
    if PROVIDER == "nvidia":
        from llama_index.embeddings.nvidia import NVIDIAEmbedding

        api_key = os.environ.get("NVIDIA_API_KEY")
        assert api_key, "study/.env에 NVIDIA_API_KEY를 채워주세요 (https://build.nvidia.com)"
        model = os.environ.get("NVIDIA_EMBED_MODEL", DEFAULT_NVIDIA_EMBED_MODEL)
        return NVIDIAEmbedding(model=model, api_key=api_key)
    else:
        from llama_index.embeddings.openai import OpenAIEmbedding

        api_key = os.environ.get("OPENAI_API_KEY")
        assert api_key, "study/.env에 OPENAI_API_KEY를 채워주세요"
        return OpenAIEmbedding(api_key=api_key)
