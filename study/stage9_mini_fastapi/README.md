# Stage 9 (선택) — 미니 FastAPI SSE 엔드포인트

## 목표
Stage 8까지 만든 스트리밍+콜백을 실제 HTTP 엔드포인트 하나로 묶습니다. DB도, 여러 대화방도 없이 **메모리에 대화 1개만** 유지하는 최소 버전이지만, 여기까지 만들고 나면 sec-insights의 [conversation.py](../../backend/app/api/endpoints/conversation.py) + [messaging.py](../../backend/app/chat/messaging.py)를 거의 그대로 읽을 수 있는 상태가 됩니다.

## ⚠️ 실제 OpenAI 크레딧 필요. `pip install -r ../requirements.txt`로 fastapi/uvicorn/sse-starlette 설치 필요.

## 할 일

`starter.py`의 TODO를 채우세요.

1. `anyio.create_memory_object_stream(100)`으로 `send_chan, recv_chan` 생성 (conversation.py와 동일한 패턴)
2. Stage 8의 에이전트 실행 로직을 `async def run_agent(question, send_chan)`으로 감싸서, 토큰이 생성될 때마다 `send_chan.send(token_so_far)`
3. `asyncio.create_task(run_agent(question, send_chan))`으로 백그라운드 실행 시작
4. `async def event_publisher(): async for msg in recv_chan: yield msg` 형태의 제너레이터 작성
5. `EventSourceResponse(event_publisher())`를 FastAPI 라우트에서 반환

## 실행

```bash
cd study/stage9_mini_fastapi
python starter.py
```

서버가 뜨면 다른 터미널에서:

```bash
curl -N "http://localhost:8010/chat?q=UBER%20%EC%A3%BC%EA%B0%80%20%EC%95%8C%EB%A0%A4%EC%A4%98"
```

`-N`은 curl이 응답을 버퍼링하지 않고 스트리밍 그대로 출력하게 하는 옵션입니다. 토큰이 하나씩 도착하는 걸 터미널에서 직접 보게 됩니다.

## 관찰 포인트

- `curl -N`으로 본 SSE 스트림의 각 줄이 `data: ...` 형태인가요? 이게 브라우저의 `EventSource`가 파싱하는 실제 프로토콜입니다.
- `conversation.py`의 `message_conversation()`과 이번 스테이지의 라우트를 나란히 놓고 비교해보세요 — DB 저장/대화 조회 부분만 없을 뿐, SSE 배선 구조는 동일합니다.
- 브라우저 개발자도구 Network 탭에서 EventStream 타입 요청을 본 적 있다면, 그게 지금 이 엔드포인트가 만드는 것과 같은 종류의 응답입니다.

## 체크포인트

- [ ] `anyio` 메모리 스트림이 "생산자 태스크"와 "SSE 응답 제너레이터" 사이를 어떻게 연결하는지 설명할 수 있다
- [ ] sec-insights의 `conversation.py`를 다시 읽었을 때 이전보다 더 잘 이해되는지 스스로 확인

## 여기까지 왔다면

`study/README.md`의 스테이지 표를 다시 보면서, 각 스테이지가 sec-insights의 어떤 파일과 대응하는지 스스로 설명해보세요. 그게 되면 이 학습은 끝난 겁니다.
