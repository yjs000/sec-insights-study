# Stage 7 — 도구의 계층적 조합 (에이전트를 다시 도구로)

## 목표
sec-insights에서 가장 핵심적인 트릭을 재현합니다: **Stage 5의 SubQuestionQueryEngine**과 **Stage 6의 FunctionAgent(가짜 주가 조회)**를 각각 도구로 다시 포장해서, 이 둘을 도구로 갖는 **최상위 에이전트**를 만듭니다.

비교 대상: [engine.py:250-301](../../backend/app/chat/engine.py) (top_level_sub_tools 조립부)

## ⚠️ 실제 LLM 필요 (무료 NVIDIA NIM 사용 가능)

## ⚠️ API 변경: 에이전트를 도구로 감싸는 방법이 달라졌습니다

원래(구식 `OpenAIAgent` 시절) sec-insights의 트릭은 "에이전트도 `QueryEngineTool.from_defaults(query_engine=agent, ...)`로 감쌀 수 있다"였습니다. `OpenAIAgent`가 `BaseQueryEngine` 인터페이스(`.query()` 메서드)까지 구현하고 있었기 때문입니다.

**`FunctionAgent`는 `BaseQueryEngine`이 아닙니다** (`.query()`가 없고 `.run()`만 있음) — 그래서 이 방법이 더 이상 안 통합니다. 대신 **"에이전트를 실행하는 함수"를 만들어 `FunctionTool`로 감싸는 방식**을 씁니다:

```python
async def ask_stock_agent(question: str) -> str:
    response = await stock_agent.run(user_msg=question)
    return str(response)

stock_price_tool = FunctionTool.from_defaults(
    fn=sync_placeholder,          # 동기 버전은 안 쓸 거라 에러만 던지는 더미
    async_fn=ask_stock_agent,     # 실제로 쓰이는 건 이쪽
    name="stock_price",
    description="주식 티커의 현재가를 조회한다.",
)
```

**핵심은 같습니다** — "에이전트 하나를 통째로 상위 에이전트의 도구 하나로 만든다"는 아이디어는 그대로고, 메커니즘만 `QueryEngineTool`(쿼리엔진 인터페이스 재사용)에서 `FunctionTool`(그냥 함수로 감싸기)로 바뀐 것입니다.

`SubQuestionQueryEngine`은 여전히 `BaseQueryEngine`이라서(에이전트가 아니라 쿼리엔진이라서) `QueryEngineTool.from_defaults(query_engine=sub_question_engine, ...)`는 **예전 그대로** 동작합니다.

## 핵심 아이디어

```
최상위 FunctionAgent
├── QueryEngineTool("document_qa") ─ SubQuestionQueryEngine (Stage 5, 그대로)
│                                      ├── QueryEngineTool("lyft")
│                                      └── QueryEngineTool("uber")
└── FunctionTool("stock_price") ─ (async_fn이 내부적으로) FunctionAgent(Stage 6) 실행
                                        └── FunctionTool(get_fake_stock_price)
```

## 할 일

`starter.py`의 TODO를 채우세요.

1. `make_stock_agent_tool()`의 `ask_stock_agent(question)` 함수 — `await stock_agent.run(user_msg=question)`을 호출하고 `str(response)` 반환
2. 위 함수를 `FunctionTool.from_defaults(fn=sync_placeholder, async_fn=ask_stock_agent, name="stock_price", description="...")`로 도구화
3. Stage 5의 `sub_question_engine`을 `QueryEngineTool.from_defaults(query_engine=..., name="document_qa", description="...")`로 감싸기
4. 이 두 도구를 가진 최상위 `FunctionAgent(tools=[...], llm=llm, verbose=True)` 생성
5. 문서 질문, 주가 질문, 무관한 질문을 각각 `await top_agent.run(user_msg=...)`로 던져서 최상위 에이전트가 알맞은 경로로 라우팅하는지 확인

## 실행

```bash
cd study/stage7_agent_of_agents
python starter.py
```

## 관찰 포인트

- `verbose=True` 로그를 보면 최상위 에이전트가 먼저 `document_qa`/`stock_price` 중 하나를 고르고, 그 안에서 다시 한 단계 더 처리(서브 질문 분해 또는 함수 호출)가 일어나는 게 보이나요? **2단계로 라우팅**되는 걸 로그로 확인하는 게 이번 스테이지의 핵심입니다.
- 한 메시지에 문서 질문과 주가 질문을 동시에 넣으면 (`"Uber 리스크 요인 알려주고 UBER 주가도 알려줘"`) 에이전트가 두 도구를 순차적으로 다 호출하나요?
- `stock_price` 도구 안에서 `stock_agent`가 또 하나의 완전한 에이전트 루프(질문 이해 → 함수 호출 판단 → `get_fake_stock_price` 실행 → 답 생성)를 통째로 도는 걸 로그에서 구분할 수 있나요?

## 체크포인트

- [ ] "에이전트를 도구로 감쌀 수 있다"가 왜 `QueryEngineTool`이 아니라 `FunctionTool`로 구현됐는지 설명할 수 있다 (`FunctionAgent`가 `BaseQueryEngine`이 아니기 때문)
- [ ] 최상위 에이전트 로그에서 2단계 라우팅(어떤 상위 도구 → 그 안에서 다시 어떤 하위 동작)을 직접 확인했다

다음: `study/stage8_streaming_callback`
