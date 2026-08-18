# Stage 6 — 미니 에이전트 만들기 (한 번에 다 붙이기)

이전 스테이지들을 하나로 합칩니다. TODO를 다 채우면 **터미널에서 직접 대화할 수 있는 미니 sec-insights**가 생깁니다.

## 이번 스테이지에서 한 번에 배우는 것

| 개념 | 어디서 쓰이나 |
|---|---|
| `FunctionTool` | 가짜 주가 조회 함수를 도구화 |
| `QueryEngineTool` + `SubQuestionQueryEngine` | Stage 5의 문서 검색을 재사용해서 도구화 |
| 에이전트를 다시 도구로 (`FunctionTool`이 내부적으로 다른 `FunctionAgent`를 실행) | "주가 담당 에이전트"를 상위 에이전트의 도구로 |
| 최상위 `FunctionAgent` | 위 도구들을 다 모아서 라우팅 |
| **`Context`로 대화 기억시키기** (신규) | REPL에서 이전 질문을 기억하고 이어서 답하게 만들기 |

비교 대상: [engine.py:204-301](../../backend/app/chat/engine.py) (`get_chat_engine()` 전체 — 이 파일이 하는 일을 통째로 재현하는 겁니다)

## ⚠️ 실제 LLM 필요 (무료 NVIDIA NIM 사용 가능)

## 새로 나오는 개념: `Context`로 멀티턴 대화 만들기

지금까지는 `agent.run(user_msg=...)`을 부를 때마다 에이전트가 "리셋"됐습니다 (이전 질문을 기억 못 함). 실제 채팅봇처럼 "그거 얼마야?" 같은 이어지는 질문에 답하려면 대화 상태를 유지해야 합니다:

```python
from workflows import Context

ctx = Context(agent)  # 이 대화 세션의 상태를 담을 그릇

response1 = await agent.run(user_msg="UBER 주가 얼마야?", ctx=ctx)
response2 = await agent.run(user_msg="그럼 LYFT는?", ctx=ctx)  # 같은 ctx를 넘기면 이전 대화를 기억함
```

`ctx`를 안 넘기면 매번 새 대화, 같은 `ctx`를 계속 넘기면 하나의 대화가 이어집니다. sec-insights가 DB에 저장된 `conversation.messages`를 매번 `chat_history`로 새로 만들어 넘기는 것([engine.py](../../backend/app/chat/engine.py) `get_chat_history()`)과 같은 문제(대화 기억)를 다른 방식(메모리 안의 `Context` 객체)으로 푸는 겁니다.

## 할 일

`starter.py`를 열어 TODO를 순서대로 채우세요. 아래는 큰 그림입니다 (Stage 5~7에서 이미 만들어봤던 부품들을 조립만 하는 겁니다):

1. **문서 검색 도구** — Stage 5의 `sub_question_engine`을 그대로 가져와서 `QueryEngineTool`로 감싸기
2. **주가 조회 에이전트** — `get_fake_stock_price` 함수를 `FunctionTool`로 감싸고, 그 도구 하나만 가진 하위 `FunctionAgent`(`stock_agent`) 만들기
3. **주가 에이전트를 다시 도구로** — `stock_agent.run()`을 호출하는 `async def ask_stock_agent(question)` 함수를 만들고 `FunctionTool`로 감싸기
4. **최상위 에이전트** — 위 두 도구(`document_qa`, `stock_price`)를 가진 `top_agent` 생성
5. **REPL 루프** — `Context(top_agent)`를 하나 만들어서, `while True:`로 사용자 입력을 받아 `await top_agent.run(user_msg=질문, ctx=ctx)`를 반복 호출. `"exit"` 입력하면 종료

## 실행

```bash
cd study/stage6_mini_agent
python starter.py
```

실행하면 프롬프트가 뜹니다. 이렇게 대화해보세요:

```
질문> Uber의 2021년 주요 리스크 요인이 뭐야?
(... 답변 ...)
질문> UBER 주가는 얼마야?
(... 답변 ...)
질문> 그럼 LYFT는?
(... 이전 질문의 맥락("주가")을 기억해서 LYFT 주가로 답하는지 확인 ...)
질문> exit
```

## 캐싱

Stage 5와 동일하게 `study/index_cache.py`로 `./storage_<provider>/`에 문서 인덱스를 캐싱합니다.

## 관찰 포인트
```
C:\Users\Family\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\llama_index\llms\nvidia\base.py:166: UserWarning: Found nvidia/nemotron-3-ultra-550b-a55b in available_models, but type is unknown and inference may fail.
  warnings.warn(
[index_cache] 캐시된 인덱스를 불러옵니다: C:\Users\Family\Documents\learning\sec-insights\study\stage6_mini_agent\storage_nvidia
2026-08-14 15:11:36,633 - INFO - Loading all indices.
미니 sec-insights 에이전트입니다. 'exit' 입력 시 종료.
예: 'Uber의 2021년 주요 리스크 요인이 뭐야?' / 'UBER 주가는 얼마야?' / '그럼 LYFT는?'

질문> Uber의 2021년 주요 리스크 요인이 뭐야?
2026-08-14 15:11:43,793 - INFO - [tick] add: AgentWorkflowStartEvent(user_msg='Uber의 2021년 주요 리스크 요인이 뭐야?', chat_history=None, memory=None, max_iterations=None, early_stopping_method=None)
2026-08-14 15:11:43,793 - INFO - [init_run:0] started from AgentWorkflowStartEvent
2026-08-14 15:11:44,203 - INFO - [init_run:0] complete with AgentInput
2026-08-14 15:11:44,203 - INFO - [tick] add: AgentInput(input=[ChatMessage(role=<MessageRole.USER: 'user'>, additional_kwargs={}, blocks=[TextBlock(block_type='text', text='Uber의 2021년 주요 리스크 요인이 뭐야?')])], current_agent_name='Agent')
2026-08-14 15:11:44,203 - INFO - [setup_agent:0] started from AgentInput
2026-08-14 15:11:44,204 - INFO - [setup_agent:0] complete with AgentSetup
2026-08-14 15:11:44,205 - INFO - [tick] add: AgentSetup(input=[ChatMessage(role=<MessageRole.USER: 'user'>, additional_kwargs={}, blocks=[TextBlock(block_type='text', text='Uber의 2021년 주요 리스크 요인이 뭐야?')])], current_agent_name='Agent')
2026-08-14 15:11:44,205 - INFO - [run_agent_step:0] started from AgentSetup
2026-08-14 15:11:44,594 - INFO - HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
2026-08-14 15:11:46,190 - INFO - [run_agent_step:0] complete with AgentOutput
2026-08-14 15:11:46,191 - INFO - [tick] add: AgentOutput(response=ChatMessage(role=<MessageRole.ASSISTANT: 'assistant'>, additional_kwargs={'tool_calls': [ChoiceDeltaToolCall(index=0, id='call-a88deb5c-9b0f-425c-8b98-0d48286b0f83', function=C...
2026-08-14 15:11:46,191 - INFO - [parse_agent_output:0] started from AgentOutput
2026-08-14 15:11:46,360 - INFO - [tick] add: ToolCall(tool_name='document_qa', tool_kwargs={'input': 'Uber 2021 major risk factors'}, tool_id='call-a88deb5c-9b0f-425c-8b98-0d48286b0f83')
2026-08-14 15:11:46,360 - INFO - [call_tool:0] started from ToolCall
2026-08-14 15:11:46,363 - INFO - [parse_agent_output:0] complete with no result
2026-08-14 15:11:51,037 - INFO - HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
Generated 1 sub questions.
[uber] Q: What are the major risk factors for Uber in 2021?
2026-08-14 15:11:51,443 - INFO - HTTP Request: POST https://integrate.api.nvidia.com/v1/embeddings "HTTP/1.1 200 OK"
2026-08-14 15:12:09,443 - INFO - HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
[uber] A: Based on the information provided, Uber faced several major risk factors in 2021:

**Geographic Concentration Risk**
The company derived a significant portion of its Gross Bookings from trips in large metropolitan areas and airport routes. In 2021, 23% of Mobility Gross Bookings came from just five metropolitan areas—Chicago, Miami, New York City, São Paulo, and London. This concentration makes the business vulnerable to economic, social, weather, regulatory conditions, and disease outbreaks in these specific locations.

**COVID-19 Pandemic Impacts**
The pandemic continued to adversely affect operations through reduced demand for Mobility offerings globally, changes in travel behavior, and persistent driver supply constraints. The emergence of variants like Omicron created ongoing uncertainty. The pandemic also caused extreme volatility in financial markets, affecting stock price and access to capital markets, while simultaneously impacting business partners and third-party vendors.

**Driver Classification Challenges**
The classification of drivers as independent contractors faced widespread legal challenges globally. Uber was involved in numerous legal proceedings—including class action lawsuits, arbitration demands, administrative charges, and government investigations—arguing that drivers should be classified as employees, workers, or quasi-employees.

**Intense Metropolitan Competition**
Strong competition in major metropolitan areas necessitated significant driver incentives and consumer discounts and promotions, affecting profitability in these key markets.

**Cascading Risk Effects**
The pandemic had the effect of heightening many other operational and financial risks, with potential for unforeseen cascading effects on business performance and financial condition.
2026-08-14 15:12:17,601 - INFO - HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
2026-08-14 15:12:17,602 - INFO - [call_tool:0] complete with ToolCallResult
2026-08-14 15:12:17,603 - INFO - [tick] add: ToolCallResult(tool_name='document_qa', tool_kwargs={'input': 'Uber 2021 major risk factors'}, tool_id='call-a88deb5c-9b0f-425c-8b98-0d48286b0f83', tool_output=ToolOutput(blocks=[TextBlock(block_ty...
2026-08-14 15:12:17,603 - INFO - [aggregate_tool_results:0] started from ToolCallResult
2026-08-14 15:12:17,778 - INFO - [aggregate_tool_results:0] complete with AgentInput
2026-08-14 15:12:17,779 - INFO - [tick] add: AgentInput(input=[ChatMessage(role=<MessageRole.USER: 'user'>, additional_kwargs={}, blocks=[TextBlock(block_type='text', text='Uber의 2021년 주요 리스크 요인이 뭐야?')])], current_agent_name='Agent')
2026-08-14 15:12:17,779 - INFO - [setup_agent:0] started from AgentInput
2026-08-14 15:12:17,780 - INFO - [setup_agent:0] complete with AgentSetup
2026-08-14 15:12:17,780 - INFO - [tick] add: AgentSetup(input=[ChatMessage(role=<MessageRole.USER: 'user'>, additional_kwargs={}, blocks=[TextBlock(block_type='text', text='Uber의 2021년 주요 리스크 요인이 뭐야?')])], current_agent_name='Agent')
2026-08-14 15:12:17,780 - INFO - [run_agent_step:0] started from AgentSetup
2026-08-14 15:12:18,062 - INFO - HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
2026-08-14 15:12:28,509 - INFO - [run_agent_step:0] complete with AgentOutput
2026-08-14 15:12:28,509 - INFO - [tick] add: AgentOutput(response=ChatMessage(role=<MessageRole.ASSISTANT: 'assistant'>, additional_kwargs={}, blocks=[ThinkingBlock(block_type='thinking', content=" user asked for Uber's 2021 major risk factor...
2026-08-14 15:12:28,509 - INFO - [parse_agent_output:0] started from AgentOutput
2026-08-14 15:12:28,786 - INFO - [result] StopEvent(result=AgentOutput(response=ChatMessage(role=<MessageRole.ASSISTANT: 'assistant'>, additional_kwargs={}, blocks=[ThinkingBlock(block_type='thinking', content=" user asked for Uber's 2021 ...
2026-08-14 15:12:28,787 - INFO - [parse_agent_output:0] complete with StopEvent

답변> Uber의 2021년 SEC 보고서(10-K)에 명시된 **주요 리스크 요인**은 다음과 같습니다.
```

**로그 분석 (성공 케이스입니다, 정상 동작):** 이 한 번의 질문에 실제로는 LLM 호출이 4번 일어났습니다.
1. `run_agent_step`(1차) — 최상위 `top_agent`가 "이 질문엔 `document_qa` 도구가 필요하다"고 판단 (`AgentOutput`에 `tool_calls` 포함) → `ToolCall(tool_name='document_qa', ...)`
2. `call_tool` 안에서 `document_qa`(=Stage 5의 `SubQuestionQueryEngine`)가 다시 자기 몫의 LLM 호출을 함 — "Generated 1 sub questions"(질문 분해), `[uber] Q: ...`(서브 질문), `[uber] A: ...`(서브 답변 생성) → `ToolCallResult`로 최상위 에이전트에 반환
3. `aggregate_tool_results` → 다시 `AgentInput`으로 돌아가 `run_agent_step`(2차) — 이번엔 도구 호출 없이 `ThinkingBlock`(추론) 후 최종 답변 생성 → `StopEvent`

즉 **"최상위 에이전트의 2단계 사이클(도구 선택→최종 종합)" 안에, "SubQuestionQueryEngine 자신의 3단계 사이클(분해→질의→종합)"이 통째로 끼워져 있는 구조**를 로그로 직접 확인하신 겁니다 — Stage 5에서 배운 3단계가 이번엔 더 큰 사이클의 한 단계(도구 호출) 안에서 재사용되는 걸 본 것.

중간에 `embeddings` 호출이 1번 있는 것도 정상입니다 — 문서 375개 청크는 캐시(`storage_nvidia/`)에서 불러왔지만, **사용자의 질문 텍스트 자체는 검색을 위해 매번 새로 임베딩**해야 하기 때문입니다 (캐싱 대상은 "문서", 캐싱 안 되는 건 "이번 질문").

- "그럼 LYFT는?"처럼 맥락이 필요한 질문에 `ctx`를 공유했을 때와 안 했을 때 답변이 어떻게 달라지나요? (실험 삼아 `ctx=ctx`를 빼고 같은 질문을 던져보세요)
- 문서 질문 → 주가 질문 → 복합 질문(둘 다 필요한 질문)을 순서대로 던져서, 매번 최상위 에이전트가 올바른 도구로 라우팅하는지 확인해보세요
- 한 도구 안에서 또 다른 에이전트 루프가 통째로 도는 것(`stock_price` 도구 → `stock_agent`가 다시 `get_fake_stock_price` 호출 여부를 스스로 판단)을 로그에서 구분할 수 있나요?

## 체크포인트

- [x] `FunctionTool`(함수 감싸기)과 `QueryEngineTool`(쿼리엔진 감싸기), 그리고 "에이전트를 함수로 감싸서 FunctionTool로 만들기" 세 가지 도구화 방식을 구분해서 설명할 수 있다
  - `get_fake_stock_price`(순수 함수) → `FunctionTool`. `sub_question_engine`(쿼리엔진, `.query()` 있음) → `QueryEngineTool`. `stock_agent`(에이전트, `.query()` 없음) → 직접 못 감싸고 `ask_stock_agent()`라는 함수로 한 번 감싼 뒤 그 함수를 다시 `FunctionTool`로 감쌈 — "에이전트는 함수라는 다리를 거쳐서만 도구가 될 수 있다"는 게 이번 스테이지의 핵심.
- [ ] `Context`가 왜 필요한지, 없으면 어떤 문제가 생기는지 실행으로 확인했다 (관찰 포인트 1번 실험 결과를 여기 적어보세요)
- [ ] sec-insights의 `get_chat_engine()`이 하는 일을 지금 만든 코드와 한 줄씩 대응시켜 설명할 수 있다

## 부록: 프롬프트 vs 네이티브 function calling (요약)

- **네이티브(모델 API 자체 기능)**: "이 도구 목록 중 뭘, 무슨 인자로 호출할지" 1회성 결정. OpenAI/Claude/Nemotron 전부 훈련 단계에서 익힌 기능이라 프롬프트 없이도 동작 (`tools=` 스키마만 넘기면 됨).
- **네이티브가 아닌 것**: "복잡한 질문을 서브 질문 여러 개로 쪼개고, 각각 도구를 호출하고, 결과를 합성"처럼 **여러 번의 API 호출을 엮는 워크플로우**. 모델은 상태가 없어서(stateless) 이런 흐름 자체를 모름 — `SubQuestionQueryEngine`이 프롬프트(지시문+예시)로 "쪼개는 척"을 유도하고, 그 결과를 파싱해서 실제 도구 호출·재호출을 **파이썬 코드가** 순서대로 수행하는 것. LlamaIndex 없이 Nemotron만 있었다면 이 흐름 자체가 일어나지 않음.
- **그래서**: 단순 도구 선택 이상의 다단계 오케스트레이션이 필요할 때 LangChain/LangGraph/LlamaIndex 같은 프레임워크가 필요해짐. 실제로 최신 LangChain(`create_agent`)과 LangGraph(`create_react_agent`)의 기본 프롬프트를 소스로 열어보니 **둘 다 기본 시스템 프롬프트가 없었음**(`system_prompt=None`이 기본값) — 순수 네이티브 tool calling에만 의존. 반면 LlamaIndex의 `SubQuestionQueryEngine`은 네이티브에 없는 기능이라 프롬프트가 필수로 내장돼있음. 즉 **"프레임워크가 프롬프트를 내장하느냐"는 그 기능이 모델 API에 원래 있느냐 없느냐에 달림.**
- **다음 학습 방향**: 오케스트레이션 자체가 핵심이라면, 결국 LangChain/LangGraph/LlamaIndex 세 라이브러리의 설계 철학·장단점 차이를 아는 게 "어떤 도구로 오케스트레이션을 만들지" 선택하는 데 필요함 (별도 학습 주제로 남겨둠).

다음: `study/stage7_streaming_web`
