# Stage 6 — 파이썬 함수를 에이전트 도구로 (FunctionTool)

## 목표
지금까지는 "검색(RAG)"만 도구로 썼습니다. 이번엔 **아무 파이썬 함수**를 에이전트가 호출할 수 있는 도구로 만듭니다. sec-insights의 `tools.py`가 polygon.io API를 호출하는 것과 같은 패턴이지만, 외부 API 키 없이 테스트할 수 있도록 가짜 주가 함수를 씁니다.

비교 대상: [tools.py](../../backend/app/chat/tools.py)

## ⚠️ 실제 LLM 필요 (무료 NVIDIA NIM 사용 가능)
에이전트가 "이 질문엔 어떤 함수를 호출해야겠다"를 판단하는 것 자체가 LLM의 function-calling 기능이라 실제 API가 필요합니다. Stage 5와 마찬가지로 `study/llm_provider.py`의 `get_llm()`을 씁니다 (`study/.env`의 `LLM_PROVIDER`로 nvidia/openai 선택).

## ⚠️ API 변경: `OpenAIAgent` → `FunctionAgent`
`llama-index-agent-openai`(구식 `OpenAIAgent`)는 이제 설치된 `llama-index-core` 버전과 호환되지 않습니다 (Stage 5 README의 "버전 업그레이드 노트" 참고). 대신 provider에 상관없이 동작하는 **`FunctionAgent`**(`llama_index.core.agent.workflow`)를 씁니다. 가장 큰 차이:
- 동기 `.chat()`이 없고 **비동기 `.run(user_msg=...)`만** 제공 — `asyncio.run(main())`으로 감싸야 합니다.
- `.run()`은 즉시 최종 답을 주지 않고 **`await`가 필요한 핸들**을 돌려줍니다 (Stage 8에서 이 핸들로 스트리밍도 다룹니다).

## 할 일

`starter.py`의 TODO를 채우세요.

1. 동기 함수 `get_fake_stock_price(ticker: str) -> str` 작성 — 미리 정의된 딕셔너리(`{"UBER": 72.5, "LYFT": 11.3}`)에서 값을 찾아 문자열로 반환. 없는 티커면 "정보 없음" 반환
2. `FunctionTool.from_defaults(fn=get_fake_stock_price, description="...")`로 도구화 (description에 "주식 티커를 받아 현재가를 반환한다" 같은 설명 필수)
3. 이 도구 하나만 가진 `FunctionAgent(tools=[tool], llm=llm, verbose=True)` 생성
4. `await agent.run(user_msg="UBER 주가 얼마야?")` 실행 → `verbose=True` 로그에서 에이전트가 실제로 함수를 호출하는 과정을 관찰
5. 이번엔 주식과 무관한 질문(`"오늘 기분 어때?"`)을 던져서 에이전트가 함수를 호출하지 *않는지* 확인

## 실행

```bash
cd study/stage6_function_tool
python starter.py
```

## 관찰 포인트

- `verbose=True` 로그에 함수 호출 시 어떤 인자(ticker 값)가 전달되나요? LLM이 "UBER 주가 얼마야?"라는 자연어에서 `ticker="UBER"`를 어떻게 뽑아내는지 확인해보세요.
- description을 지워보거나 애매하게 바꾸면 에이전트가 함수를 안 부르거나 엉뚱하게 부르는지 실험해보세요.
- 없는 티커("TSLA")를 물어보면 에이전트가 "정보 없음"을 받은 뒤 최종 답변을 어떻게 만드나요?

## 체크포인트

- [ ] `FunctionTool`과 `QueryEngineTool`의 공통점(둘 다 `description`으로 선택된다)과 차이점(하나는 검색, 하나는 임의 코드 실행)을 설명할 수 있다
- [ ] 에이전트가 "함수를 부를지 말지"를 스스로 판단한다는 걸 실행으로 확인했다
- [ ] `FunctionAgent.run()`이 `.chat()`과 달리 왜 `await`/`asyncio`가 필요한지 설명할 수 있다

다음: `study/stage7_agent_of_agents`
