# Stage 5 — QueryEngineTool + SubQuestionQueryEngine

## ⚠️ 이 스테이지부터는 실제 OpenAI 크레딧이 필요합니다

`SubQuestionQueryEngine`은 "사용자의 질문을 여러 서브 질문으로 쪼개는" 단계에서 LLM이 **구조화된 출력**(어떤 도구에 어떤 서브 질문을 보낼지 JSON 형태)을 만들어야 합니다. `MockLLM`은 진짜 추론을 하지 않고 프롬프트를 그대로 돌려주기만 해서 이 구조화된 출력을 만들 수 없습니다 — 그래서 여기서부터는 Mock으로 대체할 수 없습니다.

비용을 아끼려면:
- `study/.env`에서 모델을 `gpt-4o-mini`처럼 저렴한 모델로 설정
- 문서는 이미 있는 lyft/uber PDF 2개만 사용 (테스트 질문도 짧게)

## 목표
"복합 질문을 여러 도구에 나눠 물어보고 종합한다"는 sec-insights의 핵심 패턴을 재현합니다.

비교 대상: [engine.py:217-235](../../backend/app/chat/engine.py) (qualitative_question_engine 부분)

## 할 일

`starter.py`의 TODO를 채우세요.

1. Stage 3처럼 lyft/uber 문서를 각각 `db_document_id` 메타데이터로 태깅해서 **하나의** 인덱스로 합치기 (이번엔 진짜 `OpenAIEmbedding` 사용)
2. 문서별로 필터링된 쿼리 엔진 2개 생성 (`index.as_query_engine(filters=...)`, Stage 3 참고)
3. 각 쿼리 엔진을 `QueryEngineTool`로 래핑 — `name`은 `"lyft"`/`"uber"`, `description`은 "Lyft/Uber의 2021년 SEC 10-K 재무보고서"처럼 의미 있게 작성 (LLM이 이 설명만 보고 도구를 고릅니다!)
4. `SubQuestionQueryEngine.from_defaults(query_engine_tools=[...], verbose=True)`로 두 도구를 묶기
5. "Uber와 Lyft 중 2021년 매출이 더 큰 회사는 어디야?" 같은 **두 회사를 비교하는 질문**을 던지고, `verbose=True`가 콘솔에 출력하는 서브 질문들을 관찰

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

- [ ] `QueryEngineTool`의 `description`이 왜 중요한지 설명할 수 있다
- [ ] `SubQuestionQueryEngine`이 복합 질문을 처리하는 3단계(분해→각 도구 질의→종합)를 설명할 수 있다

다음: `study/stage6_function_tool`
