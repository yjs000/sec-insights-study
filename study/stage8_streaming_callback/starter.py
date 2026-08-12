"""
Stage 8 — 스트리밍 응답 + 콜백
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
실제 OpenAI API 키/크레딧이 필요합니다.
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from llama_index.core.tools import FunctionTool
from llama_index.core.callbacks.base import BaseCallbackHandler
from llama_index.core.callbacks.schema import CBEventType
from llama_index.core.callbacks import CallbackManager
from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI

FAKE_PRICES = {"UBER": 72.5, "LYFT": 11.3}


def get_fake_stock_price(ticker: str) -> str:
    """주어진 티커의 현재 주가를 반환한다. 없는 티커면 '정보 없음'을 반환한다."""
    price = FAKE_PRICES.get(ticker.upper())
    return "정보 없음" if price is None else f"{ticker.upper()} 현재가: ${price}"


class PrintCallbackHandler(BaseCallbackHandler):
    """이벤트 시작/종료를 콘솔에 그냥 찍기만 하는 최소 콜백 핸들러"""

    def __init__(self):
        # sec-insights의 ChatCallbackHandler처럼 너무 잦은 이벤트는 무시
        ignored = [CBEventType.CHUNKING, CBEventType.NODE_PARSING]
        super().__init__(ignored, ignored)

    def on_event_start(self, event_type: CBEventType, payload: Optional[Dict[str, Any]] = None, event_id: str = "", **kwargs: Any) -> str:
        # TODO 1: f">>> START {event_type}" 형태로 출력
        pass  # <- 여기를 채우세요
        return event_id

    def on_event_end(self, event_type: CBEventType, payload: Optional[Dict[str, Any]] = None, event_id: str = "", **kwargs: Any) -> None:
        # TODO 2: f"<<< END   {event_type}" 형태로 출력
        pass  # <- 여기를 채우세요

    def start_trace(self, trace_id: Optional[str] = None) -> None:
        pass

    def end_trace(self, trace_id: Optional[str] = None, trace_map=None) -> None:
        pass


def main():
    assert os.environ.get("OPENAI_API_KEY"), "study/.env에 OPENAI_API_KEY를 채워주세요"

    llm = OpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    stock_tool = FunctionTool.from_defaults(
        fn=get_fake_stock_price,
        description="주식 티커(예: UBER, LYFT)를 받아 현재 주가를 반환한다.",
    )

    # TODO 3: CallbackManager([PrintCallbackHandler()]) 생성
    callback_manager = None  # <- 여기를 채우세요

    agent = OpenAIAgent.from_tools(
        [stock_tool], llm=llm, verbose=False, callback_manager=callback_manager
    )

    print("=" * 20, "콜백 로그 관찰", "=" * 20)
    response = agent.chat("UBER 주가 알려줘")
    print("\n최종 답변:", response)

    print("\n" + "=" * 20, "스트리밍 관찰", "=" * 20)
    # TODO 4: agent.stream_chat("LYFT 주가 알려줘")로 스트리밍 응답 받기
    streaming_response = None  # <- 여기를 채우세요

    # TODO 5: streaming_response.response_gen을 순회하며 토큰을 그때그때 출력 (end="", flush=True)
    for token in []:  # <- streaming_response.response_gen 으로 바꾸세요
        pass


if __name__ == "__main__":
    main()
