# Stage 7 — 실시간 스트리밍 웹 데모

Stage 6에서 만든 멀티툴 에이전트를 **브라우저에서 직접 채팅할 수 있는 웹 데모**로 만듭니다. 이번엔 터미널 로그 대신 실제로 브라우저 화면에 답변이 타이핑되듯 나타나는 걸 보게 됩니다.

## 이번 스테이지에서 한 번에 배우는 것

| 개념 | 어디서 쓰이나 |
|---|---|
| `handler.stream_events()` + `AgentStream` | 토큰이 생성되는 대로 관찰 |
| `anyio` 메모리 스트림 | "에이전트 실행 태스크"와 "SSE 응답"을 연결하는 파이프 |
| FastAPI + `EventSourceResponse` | SSE 엔드포인트 |
| **비싼 초기화는 서버 시작 시 한 번만** (신규) | 에이전트/도구/인덱스는 앱 기동 시 한 번만 만들고, 요청마다 재사용 |
| **정적 HTML + `EventSource`** (신규) | 실제 브라우저에서 스트리밍 응답을 받는 프론트엔드 최소 구현 |

비교 대상: [conversation.py](../../backend/app/api/endpoints/conversation.py) + [messaging.py](../../backend/app/chat/messaging.py) + [main.py의 lifespan](../../backend/app/main.py)

## ⚠️ 실제 LLM 필요 (무료 NVIDIA NIM 사용 가능). `pip install -r ../requirements.txt`로 fastapi/uvicorn/sse-starlette 설치 필요.

## 새로 나오는 개념 1: 비싼 초기화는 한 번만

Stage 6까지는 스크립트를 실행할 때마다 도구/에이전트를 새로 만들었습니다. 웹 서버는 요청마다 이러면 안 됩니다 — sec-insights의 [main.py](../../backend/app/main.py) `lifespan()`이 서버 시작 시 벡터 스토어를 한 번만 초기화하는 것과 같은 이유입니다. 이번 스테이지는 `build_top_agent()`를 **모듈 로드 시점에 한 번만** 호출하고, 요청마다는 가벼운 `Context`만 새로 만듭니다.

## 새로 나오는 개념 2: 정적 HTML + `EventSource`

브라우저 자바스크립트의 `EventSource` API가 SSE를 네이티브로 지원합니다:

```javascript
const es = new EventSource(`/chat?q=${encodeURIComponent(question)}`);
es.onmessage = (event) => {
  answerDiv.textContent = event.data;  // 서버가 보낼 때마다 계속 갱신
};
```

`curl -N`으로 보던 것과 같은 프로토콜을, 이번엔 진짜 브라우저 화면에서 봅니다.

## 할 일

`starter.py`의 TODO를 채우세요.

1. `run_agent(question, send_chan, ctx)` — `handler = top_agent.run(user_msg=question, ctx=ctx)`로 시작, `async for event in handler.stream_events():`로 `AgentStream`이면 누적된 텍스트를 `send_chan.send(...)`
2. `/chat` 라우트 — `anyio.create_memory_object_stream(100)` 생성 → `asyncio.create_task(run_agent(...))` → `EventSourceResponse(event_publisher())` 반환 (Stage 6~7 이전 패턴과 동일)
3. `/` 라우트 — `static/chat.html` 파일을 읽어 `HTMLResponse`로 반환
4. `static/chat.html`의 TODO — `fetch` 대신 `EventSource`로 `/chat` 엔드포인트 연결하고, `onmessage`에서 답변 영역 텍스트 갱신

## 실행

```bash
cd study/stage7_streaming_web
python starter.py
```

서버가 뜨면 브라우저에서 `http://localhost:8010` 을 엽니다. 질문을 입력하고 전송하면 답변이 실시간으로 타이핑되듯 나타나야 합니다.

## 관찰 포인트

- 브라우저 개발자도구 Network 탭에서 `/chat` 요청의 타입이 `eventsource`로 보이나요? 응답 본문이 `data: ...` 줄들로 계속 쌓이는 걸 확인해보세요.
- 서버를 껐다 켜지 않고 같은 서버에 여러 질문을 연달아 보내면, 두 번째 질문부터는 인덱스를 다시 만드나요 (로그로 확인)? "한 번만 초기화"가 실제로 지켜지는지 확인하는 방법입니다.
- 지금 이 데모는 요청마다 새 `Context`를 만들어서 대화가 이어지지 않습니다. Stage 6의 REPL처럼 여러 턴을 기억하게 하려면 무엇이 필요할지 생각해보세요 (힌트: 브라우저 세션/쿠키별로 `Context`를 저장해야 함 — sec-insights가 `conversation_id`로 DB에서 매번 히스토리를 불러오는 것과 같은 문제).
 -> 왜 세션쿠키에 저장해? db에저장하면안돼? 세션쿠키에 저장하면 껐다키면 날라가잖아
   -> **답 (정정)**: 실제 sec-insights 코드를 다시 확인해보니 **쿠키를 아예 안 씁니다** — 이전 답변이 틀렸습니다. 대신 `conversation_id`가 **URL 경로 자체**에 들어있습니다 (`/conversation/{id}`, [\[id\].tsx](../../frontend/src/pages/conversation/[id].tsx) 참고). 즉:
   - 새 대화를 만들면 `POST /api/conversation/`으로 `conversation_id`(UUID)를 발급받고, 프론트가 `router.push`로 `/conversation/<그 id>` 페이지로 이동한다.
   - 그 페이지의 URL 자체가 "세션 식별자"다. 새로고침해도 URL이 안 바뀌니 `conversationId`가 유지되고, 브라우저를 껐다 켜도 **그 URL을 다시 열기만 하면** 똑같은 대화로 돌아온다 (즐겨찾기/공유 가능 — 실제로 "Share" 버튼과 `ShareLinkModal`이 있음).
   - 메시지를 보낼 때도 `GET /api/conversation/{conversation_id}/message?user_message=...`처럼 id가 URL 경로에 박혀서 나간다 ([conversation.py](../../backend/app/api/endpoints/conversation.py)의 `message_conversation`).
   - DB에는 대화 내용(`Message` 테이블)이 저장되고, 서버는 매 요청마다 URL의 `conversation_id`로 DB에서 히스토리를 조회한다.
   - 즉 "세션 유지"의 정체는 쿠키가 아니라 **URL(라우팅)** 이었다 — 브라우저 상태에 의존하지 않아서 링크 공유나 새 기기에서 열기도 자연스럽게 되는 장점이 있다.

## 체크포인트

- [x] 왜 에이전트/도구/인덱스를 요청마다 새로 만들면 안 되는지 설명할 수 있다
   -> **답**: 인덱스 빌드(PDF 파싱 + 임베딩 계산 + 벡터 인덱스 생성)는 수 초~수십 초 걸리는 무거운 작업이다. 요청마다 새로 만들면 (1) 매 질문마다 그 시간만큼 응답이 늦어지고, (2) 같은 문서를 매번 다시 읽고 임베딩 API를 반복 호출해서 비용이 낭비되고, (3) 동시 요청이 여러 개 오면 서버가 계속 인덱스를 다시 굽느라 CPU/메모리도 낭비된다. 그래서 `top_agent`는 모듈이 처음 로드되는 시점(서버 프로세스 시작 시점)에 딱 한 번만 만들고, 요청마다는 가벼운 `Context(top_agent)`만 새로 만든다. sec-insights의 [main.py](../../backend/app/main.py) `lifespan()`이 서버 시작 시 벡터스토어를 한 번만 초기화하는 것과 같은 이유.
- [x] `EventSource`가 SSE 응답을 어떻게 소비하는지 설명할 수 있다
   -> **답**: `EventSource`는 일반 HTTP GET 연결을 하나 열어둔 채로, 서버가 `data: ...\n\n` 형식으로 계속 흘려보내는 텍스트를 자동으로 파싱해서 `message` 이벤트로 발생시킨다. `fetch`처럼 응답을 한 번에 받는 게 아니라, 연결이 열려있는 동안 서버가 보낼 때마다 `onmessage`가 여러 번 호출된다 (연결이 끊기면 자동 재연결도 시도하는 게 fetch 스트리밍과의 차이). 이번 stage에서는 `run_agent`가 `handler.stream_events()`로 `AgentStream`(토큰) 이벤트를 받을 때마다 누적된 텍스트를 `send_chan.send()`로 보내고, 그게 SSE로 브라우저에 전달되어 `EventSource.onmessage`가 `answerDiv.textContent`를 갱신한다.
   
- [x] 지금까지 만든 8개 스테이지가 sec-insights의 어떤 파일들과 대응하는지 스스로 설명할 수 있다 (`study/README.md`의 표 참고)
- 최상위 에이저트 -> context -> tool로 두개의 에이전트를 돌리고 -> 합쳐서 SEE로 응답
   -> **피드백**: 큰 그림은 맞는데 두 군데를 짚어야 한다.
   1. **"두 개의 에이전트를 돌린다"는 정확하지 않다.** `top_agent`가 가진 tool은 두 개(`document_qa`, `stock_price`)지만, 그중 실제로 "에이전트"인 건 `stock_price` 하나뿐이다 (`build_stock_price_tool` 안에서 `stock_agent = FunctionAgent(...)`를 만들어 감싼 것 — solution.py 91행). `document_qa`는 에이전트가 아니라 `SubQuestionQueryEngine`을 감싼 `QueryEngineTool`이다 (질문을 쪼개서 여러 벡터 인덱스에 물어보고 합치긴 하지만, LLM이 도구를 "선택"하는 에이전트 루프는 아님). 그래서 정확히는: 최상위 에이전트 1개가 상황에 따라 "쿼리엔진 도구" 또는 "중첩 에이전트 도구" 둘 중 하나(또는 둘 다)를 호출하는 구조.
   2. **오타**: SEE -> **SSE** (Server-Sent Events).

   정정한 전체 플로우: 브라우저가 질문 전송 -> `EventSource`로 `/chat?q=...` 연결 -> FastAPI가 `Context(top_agent)` 생성 -> `top_agent.run(user_msg=question, ctx=ctx)`로 handler 획득 -> top_agent가 질문을 보고 필요한 tool(`document_qa`와/또는 `stock_price`)을 골라 호출 -> 그 결과들을 top_agent가 다시 종합해 최종 답변 토큰을 생성 -> `handler.stream_events()`가 `AgentStream` 이벤트로 토큰을 흘려보낼 때마다 누적 텍스트를 `send_chan.send()` -> FastAPI가 그걸 SSE(`data: ...\n\n`)로 응답 -> 브라우저 `EventSource.onmessage`가 받아서 화면 갱신.

   **8개 스테이지 전체 매핑** (`study/README.md` 표 기준):
   | Stage | sec-insights 대응 파일 |
   |---|---|
   | 0 (로드→인덱스→질의) | [engine.py](../../backend/app/chat/engine.py) 전체 뼈대 |
   | 1 (전역 `Settings`) | [llama_index_settings.py](../../backend/app/llama_index_settings.py) |
   | 2 (인덱스 저장/재로딩) | `engine.py`의 `build_doc_id_to_index_map()`, 이번 stage의 [index_cache.py](../index_cache.py) |
   | 3 (멀티문서 + 필터) | `engine.py`의 `index_to_query_engine()`, 이번 stage의 `DOC_ID_KEY` 필터 |
   | 4 (답변 합성 프롬프트) | [qa_response_synth.py](../../backend/app/chat/qa_response_synth.py) |
   | 5 (`SubQuestionQueryEngine`) | `engine.py` 230행대, 이번 stage의 `build_document_qa_tool` |
   | 6 (`FunctionTool` + 최상위 에이전트 + `Context`) | `engine.py`의 `get_chat_engine()` |
   | 7 (스트리밍 + SSE + 브라우저) | [conversation.py](../../backend/app/api/endpoints/conversation.py) + [messaging.py](../../backend/app/chat/messaging.py) + [main.py](../../backend/app/main.py)의 `lifespan()` |

   3단 요약: Stage 0~4 = 인덱스/검색 기초, Stage 5~6 = 도구화·에이전트 조합, Stage 7 = 그걸 실제 웹 서버로 서빙.

## 여기까지 왔다면

`study/README.md`의 스테이지 표를 다시 보면서, 각 스테이지가 sec-insights의 어떤 파일과 대응하는지 스스로 설명해보세요. 그게 되면 이 학습은 끝난 겁니다.
