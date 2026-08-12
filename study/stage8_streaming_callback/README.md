# Stage 8 — 스트리밍 응답 + 콜백

## 목표
지금까지는 `agent.chat()`/`query_engine.query()`로 완성된 답변을 한 번에 받았습니다. 이번엔 (1) 토큰이 생성되는 대로 터미널에 실시간으로 찍히는 스트리밍과, (2) 에이전트 내부에서 무슨 일이 일어나는지 이벤트로 관찰하는 콜백을 재현합니다. 이 둘을 합치면 sec-insights의 SSE 응답과 거의 같은 정보를 터미널에서 볼 수 있습니다.

비교 대상: [messaging.py](../../backend/app/chat/messaging.py)

## ⚠️ 실제 OpenAI 크레딧 필요

## 할 일

`starter.py`의 TODO를 채우세요.

### Part A — 스트리밍
1. Stage 6의 `stock_agent`(또는 Stage 7의 `top_agent`)를 재사용
2. `agent.stream_chat(question)`을 호출 (동기 버전. 비동기가 궁금하면 `await agent.astream_chat(...)` + `async for`도 시도)
3. `response.response_gen`을 순회하며 `print(token, end="", flush=True)`로 토큰 단위 출력

### Part B — 콜백
4. `BaseCallbackHandler`를 상속한 `PrintCallbackHandler` 클래스 작성 — `on_event_start`에서 `print(f">>> {event_type}")` 만 찍기
5. `CallbackManager([PrintCallbackHandler()])`를 만들어 `Settings.callback_manager`에 등록 (또는 에이전트 생성 시 `callback_manager=` 인자로 직접 전달)
6. 질문을 하나 던지고, 콘솔에 어떤 이벤트 타입들이 어떤 순서로 찍히는지 관찰

## 실행

```bash
cd study/stage8_streaming_callback
python starter.py
```

## 관찰 포인트

- 스트리밍 출력이 한 번에 "훅" 나오나요, 아니면 진짜로 토큰 단위로 조금씩 나오나요? (네트워크 지연으로 몇 단어씩 뭉쳐 나올 수도 있습니다 — 정상입니다)
- 콜백 로그에 `FUNCTION_CALL`, `LLM`, `AGENT_STEP` 같은 이벤트가 찍히나요? 어떤 순서로 발생하나요?
- sec-insights의 `ChatCallbackHandler`([messaging.py](../../backend/app/chat/messaging.py))는 `CHUNKING`, `NODE_PARSING` 이벤트를 일부러 무시합니다. 여러분의 `PrintCallbackHandler`에도 같은 필터를 적용해 로그가 얼마나 깔끔해지는지 비교해보세요.

## 체크포인트

- [ ] `astream_chat()`과 `chat()`의 차이를 설명할 수 있다
- [ ] `BaseCallbackHandler`가 에이전트 실행의 "중간 상태"를 어떻게 노출하는지 실행으로 확인했다

다음: `study/stage9_mini_fastapi` (선택)
