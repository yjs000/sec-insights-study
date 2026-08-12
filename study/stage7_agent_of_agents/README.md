# Stage 7 — 도구의 계층적 조합 (에이전트를 다시 도구로)

## 목표
sec-insights에서 가장 핵심적인 트릭을 재현합니다: **Stage 5의 SubQuestionQueryEngine**과 **Stage 6의 FunctionTool 에이전트**를 각각 `QueryEngineTool`로 다시 포장해서, 이 둘을 도구로 갖는 **최상위 에이전트**를 만듭니다.

비교 대상: [engine.py:250-301](../../backend/app/chat/engine.py) (top_level_sub_tools 조립부)

## ⚠️ 실제 OpenAI 크레딧 필요

## 핵심 아이디어

```
최상위 OpenAIAgent
├── QueryEngineTool("qualitative") ─ SubQuestionQueryEngine (Stage 5)
│                                      ├── QueryEngineTool("lyft")
│                                      └── QueryEngineTool("uber")
└── QueryEngineTool("quantitative") ─ OpenAIAgent (Stage 6)
                                        └── FunctionTool(get_fake_stock_price)
```

`QueryEngineTool.from_defaults(query_engine=agent, ...)`처럼, **에이전트도 쿼리엔진처럼 감쌀 수 있습니다** (`Agent`가 `BaseQueryEngine` 인터페이스를 구현하기 때문). 이 덕분에 "쿼리엔진 안에 에이전트, 에이전트 안에 쿼리엔진"을 임의 깊이로 쌓을 수 있습니다.

## 할 일

`starter.py`의 TODO를 채우세요.

1. Stage 5의 `sub_question_engine`(lyft/uber 문서 검색)을 만들기
2. Stage 6의 `stock_agent`(가짜 주가 함수 에이전트)를 만들기
3. `QueryEngineTool.from_defaults(query_engine=sub_question_engine, name="document_qa", description="Lyft/Uber 문서 내용에 대한 질문에 답한다")`
4. `QueryEngineTool.from_defaults(query_engine=stock_agent, name="stock_price", description="주식 현재가를 조회한다")`
5. 이 두 도구를 가진 최상위 `OpenAIAgent.from_tools([...], verbose=True)` 생성
6. 문서 질문, 주가 질문, 무관한 질문을 각각 던져서 최상위 에이전트가 알맞은 경로로 라우팅하는지 확인

## 실행

```bash
cd study/stage7_agent_of_agents
python starter.py
```

## 관찰 포인트

- `verbose=True` 로그를 보면 최상위 에이전트가 먼저 `document_qa`/`stock_price` 중 하나를 고르고, 그 안에서 다시 한 단계 더 처리(서브 질문 분해 또는 함수 호출)가 일어나는 게 보이나요? **2단계로 라우팅**되는 걸 로그로 확인하는 게 이번 스테이지의 핵심입니다.
- 한 메시지에 문서 질문과 주가 질문을 동시에 넣으면 (`"Uber 리스크 요인 알려주고 UBER 주가도 알려줘"`) 에이전트가 두 도구를 순차적으로 다 호출하나요?

## 체크포인트

- [ ] "에이전트를 QueryEngineTool로 감쌀 수 있다"는 것의 의미를 설명할 수 있다
- [ ] 최상위 에이전트 로그에서 2단계 라우팅(어떤 상위 도구 → 그 안에서 다시 어떤 하위 동작)을 직접 확인했다

다음: `study/stage8_streaming_callback`
