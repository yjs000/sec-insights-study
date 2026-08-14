# Stage 5 — QueryEngineTool + SubQuestionQueryEngine

## ⚠️ 이 스테이지부터는 실제 LLM이 필요합니다 (무료 NVIDIA NIM 사용 가능)

`SubQuestionQueryEngine`은 "사용자의 질문을 여러 서브 질문으로 쪼개는" 단계에서 LLM이 **구조화된 출력**(어떤 도구에 어떤 서브 질문을 보낼지)을 만들어야 합니다. `MockLLM`은 진짜 추론을 하지 않고 프롬프트를 그대로 돌려주기만 해서 이 구조화된 출력을 만들 수 없습니다 — 그래서 여기서부터는 Mock으로 대체할 수 없습니다.

**Stage 5부터는 `study/llm_provider.py`를 통해 LLM/임베딩을 가져옵니다.** `study/.env`의 `LLM_PROVIDER`로 프로바이더를 고릅니다:
- `LLM_PROVIDER=nvidia` (추천, 무료) — [build.nvidia.com](https://build.nvidia.com)에서 API 키 발급. 기본 모델은 `nvidia/nemotron-3-ultra-550b-a55b`(2026-06 공개, 550B, tool calling 지원).
- `LLM_PROVIDER=openai` (유료) — 기존 `OPENAI_API_KEY` 사용.

## ⚠️ 버전 업그레이드 노트

NVIDIA NIM 연동 패키지(`llama-index-llms-nvidia`)가 `llama-index-core>=0.13`을 요구해서, **Stage 5부터는 `study/`의 venv가 core 0.14대로 업그레이드되어 있습니다** (Stage 0~4는 sec-insights 백엔드와 버전을 맞춘 0.12.23을 그대로 씁니다 — `study/requirements.txt` 참고). 이 업그레이드 때문에 구식 `OpenAIAgent`(`llama-index-agent-openai`)가 더 이상 설치조차 안 되고, 대신 **`FunctionAgent`**(`llama_index.core.agent.workflow`, provider 무관한 범용 에이전트)를 씁니다. 같은 이유로 `SubQuestionQueryEngine`의 질문 분해기도 OpenAI 전용 `OpenAIQuestionGenerator` 대신 범용 `LLMQuestionGenerator`를 명시적으로 넘깁니다.

## 목표
"복합 질문을 여러 도구에 나눠 물어보고 종합한다"는 sec-insights의 핵심 패턴을 재현합니다.

비교 대상: [engine.py:217-235](../../backend/app/chat/engine.py) (qualitative_question_engine 부분)

## 할 일

`starter.py`의 TODO를 채우세요.

1. Stage 3처럼 lyft/uber 문서를 각각 `db_document_id` 메타데이터로 태깅해서 **하나의** 인덱스로 합치기 (`llm_provider.get_embed_model()`로 실제 임베딩 모델 사용)
2. 문서별로 필터링된 쿼리 엔진 2개 생성 (`index.as_query_engine(filters=...)`, Stage 3 참고)
3. 각 쿼리 엔진을 `QueryEngineTool`로 래핑 — `name`은 `"lyft"`/`"uber"`, `description`은 "Lyft/Uber의 2021년 SEC 10-K 재무보고서"처럼 의미 있게 작성 (LLM이 이 설명만 보고 도구를 고릅니다!)
4. `LLMQuestionGenerator.from_defaults(llm=llm)`로 질문 분해기 생성
5. `SubQuestionQueryEngine.from_defaults(query_engine_tools=[...], question_gen=question_gen, verbose=True)`로 두 도구를 묶기
6. "Uber와 Lyft 중 2021년 매출이 더 큰 회사는 어디야?" 같은 **두 회사를 비교하는 질문**을 던지고, `verbose=True`가 콘솔에 출력하는 서브 질문들을 관찰

## 실행

```bash
cd study/stage5_sub_question
python starter.py
```

## 관찰 포인트

- 콘솔에 어떤 서브 질문들이 자동으로 생성됐나요? (예: "What was Lyft's 2021 revenue?", "What was Uber's 2021 revenue?")
- 서브 질문이 각각 어떤 도구(`lyft`/`uber`)로 라우팅됐나요?
- `description`을 일부러 애매하게 바꿔보면 (예: `"문서에 대한 정보"`) 라우팅이 이상해지는지 실험해보세요 — description의 역할을 체감하는 가장 좋은 방법입니다.

## 체크포인트

- [x] `QueryEngineTool`의 `description`이 왜 중요한지 설명할 수 있다
 : 그래야 description을 보고 llm이 tool을 선택하니까.
   -> 이것도 description적는것도 사실 LLM이 하는게 더 나을듯.
   - [x] **맞는 방향입니다.** 정확히 하는 사람도 있습니다 — 문서의 docstring/README를 LLM에게 요약시켜 description을 자동 생성하는 패턴이 실무에서도 흔합니다. 다만 **사람 검수는 남겨두는 걸 추천**합니다: description이 애매하면 라우팅이 틀려도 에러가 안 나고 "그냥 조용히 엉뚱한 도구가 선택"되기 때문에(예외가 안 터지니 디버깅이 오래 걸림) — 자동 생성하더라도 최소 한 번은 실제 질문 몇 개로 라우팅이 맞는지 확인하는 과정이 필요합니다.
- [x] `SubQuestionQueryEngine`이 복합 질문을 처리하는 3단계(분해→각 도구 질의→종합)를 설명할 수 있다
 : 모르곘어.
   - [x] **답:** ① **분해(decompose)** — LLM이 원본 질문을 읽고 "이 질문에 답하려면 어떤 하위 질문들을 각각 어떤 도구에 물어봐야 하는지"를 구조화된 형태(질문 텍스트 + 대상 도구 이름)로 생성합니다 (내부적으로 `LLMQuestionGenerator`/`OpenAIQuestionGenerator`가 담당). ② **각 도구 질의** — 생성된 서브 질문 개수만큼 해당 `QueryEngineTool`을 각각 호출합니다 (`use_async=True`면 동시에 병렬 실행). ③ **종합(synthesize)** — 모든 (서브질문, 서브답변) 쌍을 `response_synthesizer`에 넘겨서 원래 질문에 대한 하나의 최종 답변 문장으로 합칩니다. 이 3단계는 아래 질문 2의 로그에서 그대로 순서대로 관찰할 수 있습니다.

다음: `study/stage6_function_tool`


## 질문
1. verbose=true는 뭐야?
   - [x] LlamaIndex의 에이전트/쿼리엔진 대부분이 갖고 있는 공통 옵션입니다. `False`(기본값)면 최종 결과만 출력되고, `True`면 **내부에서 일어나는 중간 단계들을 콘솔에 실시간으로 print**합니다 — 이번 스테이지 기준으로는 생성된 서브 질문들, 각 서브 질문이 어느 도구로 갔는지, 각 도구의 중간 응답 등이 찍힙니다. 별도 설정 없이 그냥 켜기만 하면 되는 가장 쉬운 디버깅 수단입니다.
2. `response = sub_question_engine.query(question)` 내부 과정을 사용자가 눈으로 볼 수 있어?
   - [x] **네, 지금 당장은 `verbose=True`로 콘솔 출력**을 보는 게 가장 쉬운 방법입니다 (질문 1 참고). 더 구조화된 방식도 있습니다: `CallbackManager`에 `BaseCallbackHandler`를 등록하면 `SUB_QUESTION`, `FUNCTION_CALL` 같은 이벤트가 코드로 잡히는데, sec-insights의 [messaging.py](../../backend/app/chat/messaging.py) `ChatCallbackHandler`가 정확히 이걸 이용해서 서브 질문 진행상황을 실시간으로 프론트엔드까지 SSE로 흘려보냅니다 — 이건 **Stage 8**에서 직접 만들어봅니다.