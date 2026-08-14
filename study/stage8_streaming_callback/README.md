# Stage 8 — 스트리밍 응답 + 이벤트 관찰

## 목표
지금까지는 `agent.run()`이 끝날 때까지 기다려서 완성된 답변을 한 번에 받았습니다. 이번엔 (1) 토큰이 생성되는 대로 터미널에 실시간으로 찍히는 스트리밍과, (2) 에이전트 내부에서 무슨 일이 일어나는지(도구 호출 등) 이벤트로 관찰하는 걸 재현합니다. 이 둘을 합치면 sec-insights의 SSE 응답과 거의 같은 정보를 터미널에서 볼 수 있습니다.

비교 대상: [messaging.py](../../backend/app/chat/messaging.py)

## ⚠️ 실제 LLM 필요 (무료 NVIDIA NIM 사용 가능)

## ⚠️ API 변경: `BaseCallbackHandler` → Workflow 이벤트 스트림

sec-insights([messaging.py](../../backend/app/chat/messaging.py))는 `BaseCallbackHandler`를 상속해서 `on_event_start`/`on_event_end`로 중간 이벤트를 잡습니다 — 이건 구식 `OpenAIAgent` 시절의 콜백 시스템입니다. `FunctionAgent`는 **Workflow** 기반이라 다른 방식으로 관찰합니다: `agent.run(...)`이 돌려주는 핸들의 `handler.stream_events()`를 순회하면 스트리밍 토큰과 도구 호출 이벤트가 **같은 스트림 안에서** 순서대로 나옵니다. 콜백 등록 없이 그냥 순회만 하면 됩니다 — 오히려 이전보다 더 단순해졌습니다.

주요 이벤트 타입 (`llama_index.core.agent.workflow`에서 import):
- **`AgentStream`** — LLM이 생성 중인 토큰 조각 (`event.delta`)
- **`ToolCall`** — 도구 호출이 시작될 때 (`event.tool_name`, `event.tool_kwargs`)
- **`ToolCallResult`** — 도구 호출이 끝났을 때 (`event.tool_output`)

## 할 일

`starter.py`의 TODO를 채우세요.

1. Stage 6의 `stock_tool`/`llm`로 `FunctionAgent` 생성
2. `handler = agent.run(user_msg=question)` 호출 (아직 `await` 하지 않음 — 핸들만 받음)
3. `async for event in handler.stream_events():`로 순회하며 `AgentStream`/`ToolCall`/`ToolCallResult`를 각각 다르게 출력
4. `final_response = await handler`로 스트림이 끝난 뒤 최종 결과 받기

## 실행

```bash
cd study/stage8_streaming_callback
python starter.py
```

## 관찰 포인트

- `AgentStream`의 `event.delta`가 한 번에 "훅" 나오나요, 아니면 진짜로 토큰 단위로 조금씩 나오나요? (네트워크 지연으로 몇 단어씩 뭉쳐 나올 수도 있습니다 — 정상입니다)
- `ToolCall` → (실제 함수 실행) → `ToolCallResult` → 그 다음 `AgentStream`(최종 답변 생성) 순서로 이벤트가 나오나요?
- sec-insights의 `ChatCallbackHandler`는 `CHUNKING`, `NODE_PARSING` 이벤트를 일부러 무시합니다(너무 잦아서). 이번 방식은 애초에 `AgentStream`/`ToolCall`/`ToolCallResult` 몇 종류만 나오므로 그런 필터링이 따로 필요 없다는 것도 비교해보세요.

## 체크포인트

- [ ] `handler = agent.run(...)`(아직 안 끝남) vs `await handler`(끝날 때까지 기다려 최종 결과)의 차이를 설명할 수 있다
- [ ] `stream_events()`가 에이전트 실행의 "중간 상태"를 어떻게 노출하는지 실행으로 확인했다

다음: `study/stage9_mini_fastapi` (선택)
