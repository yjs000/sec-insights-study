# Stage 4 — 답변 합성 프롬프트 커스터마이징

## 목표
검색된 청크를 실제 답변 문장으로 바꾸는 "합성(synthesis)" 단계의 프롬프트를 커스터마이징합니다. sec-insights가 왜 `qa_response_synth.py`를 따로 만들었는지 직접 확인합니다.

비교 대상: [qa_response_synth.py](../../backend/app/chat/qa_response_synth.py)

## 배경 지식

`get_response_synthesizer()`는 두 개의 프롬프트 템플릿을 받습니다:
- `text_qa_template` — 검색된 첫 청크(들)로 최초 답변을 만들 때 쓰는 프롬프트
- `refine_template` — 다음 청크가 왔을 때 기존 답을 "정련(refine)"할 때 쓰는 프롬프트

이번 스테이지는 `MockLLM`을 씁니다. `MockLLM`은 실제 추론을 하지 않고 **받은 프롬프트를 거의 그대로 돌려주기 때문에**, 오히려 "내가 만든 템플릿이 최종적으로 LLM에 어떤 텍스트로 전달되는지"를 눈으로 정확히 확인하기 좋습니다 (Stage 0에서 이미 한 번 봤던 방식입니다).

## 할 일

`starter.py`의 TODO를 채우세요.

1. 기본 `index.as_query_engine()`으로 질문 → 출력되는 프롬프트(Mock 답변)를 확인 (기본 템플릿)
2. `QuestionAnswerPrompt`로 커스텀 `text_qa_template` 작성: "너는 SEC 재무제표 전문 애널리스트다. 반드시 문서에 나온 숫자를 인용해서 답하라"는 지시를 담아서
3. `get_response_synthesizer(text_qa_template=커스텀템플릿)`로 새 synthesizer 생성
4. `index.as_query_engine(response_synthesizer=커스텀_synth)`로 다시 질문 → 프롬프트에 내가 넣은 지시문이 실제로 포함되는지 확인

## 실행

```bash
cd study/stage4_prompt_synth
python starter.py
```

## 관찰 포인트

- 기본 템플릿과 커스텀 템플릿의 출력을 나란히 비교했을 때, 내가 추가한 지시문이 어디에 삽입되나요?
- `{context_str}`, `{query_str}` 같은 자리표시자는 언제 실제 값으로 채워지나요? (힌트: 템플릿을 만드는 시점 vs `.query()` 실행 시점)
  - [x] 답: `.query()` 실행 시점. 맞습니다 — 템플릿 문자열을 만드는 시점(`QuestionAnswerPrompt(...)` 호출)에는 아직 빈 자리표시자일 뿐이고, 실제 검색된 청크(`context_str`)와 사용자 질문(`query_str`)이 채워지는 건 `.query(question)`이 실행되면서 검색이 끝난 직후입니다.
- sec-insights의 [qa_response_synth.py](../../backend/app/chat/qa_response_synth.py)를 다시 보면, `doc_titles`는 파이썬 f-string으로 **지금** 채워지고 `{{context_str}}`(이중 중괄호)는 **나중에** LlamaIndex가 채운다는 걸 구분할 수 있나요?
  - [x] **답:** `qa_response_synth.py`의 템플릿 문자열은 **f-string**(`f"""..."""`)으로 작성됩니다. f-string 안에서 `{doc_titles}`처럼 중괄호 하나면 "지금 이 파이썬 코드가 실행되는 시점"에 바로 값이 치환됩니다. 반면 `{{context_str}}`처럼 이중 중괄호는 f-string 문법상 "리터럴 중괄호 하나를 출력하라"는 이스케이프라서, f-string이 평가된 결과물엔 `{context_str}`(단일 중괄호)로 남습니다. 이 결과 문자열이 `QuestionAnswerPrompt(template=...)`에 들어가고, 그 안의 `{context_str}`을 LlamaIndex가 **나중에**(`.query()` 시점) 채웁니다. 즉 이중 치환입니다: ① 지금 파이썬 f-string이 `doc_titles` 채움 → ② 나중에 LlamaIndex가 `context_str`/`query_str` 채움. `starter.py`/`solution.py`는 f-string이 아니라 일반 `"""..."""` 문자열을 썼기 때문에 `{context_str}`을 그냥 단일 중괄호로 바로 썼다는 차이도 있습니다.

## 체크포인트

- [x] `text_qa_template`과 `refine_template`의 역할 차이를 설명할 수 있다
  - `text_qa_template`: 검색된 첫 청크(들)로 **최초** 답변을 만들 때 쓰는 프롬프트. `refine_template`: 다음 청크가 추가로 왔을 때 기존 답을 그 청크 내용으로 **다듬을지 말지** 판단하는 프롬프트. top_k=1이면 청크가 하나뿐이라 refine 단계 자체가 발생하지 않습니다 (아래 질문 2 참고).
- [x] 커스텀 프롬프트가 실제로 LLM에 어떻게 전달되는지 출력으로 확인했다
  - MockLLM 출력에서 "질문:"/"답변:" 앞에 우리가 넣은 지시문이 그대로 찍힌 걸 확인함.

다음: `study/stage5_sub_question` — 여기부터는 실제 OpenAI 크레딧이 필요합니다 (MockLLM으로는 구조적 출력이 필요한 기능을 테스트할 수 없습니다).

## 질문
1. `{}`, `{{}}` 연산자가 뭐지?
   - [x] 파이썬 `str.format()`/f-string 문법입니다. `{이름}`은 "이 자리에 `이름`이라는 값을 채워 넣어라"는 **자리표시자(placeholder)**. `{{`, `}}`는 진짜 중괄호 문자 `{`, `}` 하나를 출력하고 싶을 때 쓰는 **이스케이프**(중괄호 자체가 `.format()`/f-string에서 특수문자라서 두 번 써야 리터럴이 됨). `starter.py`의 템플릿은 f-string이 아닌 **일반 문자열**(`"""..."""`)이라서 `{{answer}}`를 넣어도 이스케이프가 그 시점엔 적용되지 않고, 그냥 문자 그대로 `{{answer}}`가 문자열에 남습니다.
2. 답변이 이렇게 나오는데? answer가 안 나와. 템플릿은 나와.
   - [x] **정확한 원인:** `{{answer}}`는 애초에 LlamaIndex가 인식하는 자리표시자가 아닙니다. LlamaIndex는 템플릿 문자열을 `SafeFormatter`라는 자체 포매터로 처리하는데, 이건 자기가 아는 키(`context_str`, `query_str`)만 채우고 **모르는 `{{answer}}`는 그냥 원문 그대로 놔둡니다** (에러도 안 내고, 파이썬 표준 `str.format()`처럼 `{{`→`{`로 풀어주지도 않습니다). 그래서 출력에 `{{answer}}`가 손 안 댄 채로 그대로 찍힌 겁니다.
   - **더 중요한 개념:**애초에 "답변이 채워지는 슬롯"이라는 게 이 템플릿 안에는 없습니다. 이 템플릿 전체가 만드는 건 **LLM에게 보낼 입력 프롬프트**일 뿐이고, "진짜 답변"은 그 프롬프트를 받은 LLM이 **새로 생성해서 이어붙이는 별도의 출력**입니다 (실제 OpenAI라면 "답변:" 뒤에 이어지는 텍스트를 모델이 스스로 만들어냄). `MockLLM`은 추론을 안 하고 받은 프롬프트를 그대로 돌려주기만 하니, "답변:" 뒤에 아무것도 새로 안 생기고 우리가 넣은 리터럴 텍스트(`{{answer}}`)만 남아있던 것입니다.
   - **확인해보고 싶다면:** `Settings.llm = MockLLM()` 대신 `Settings.llm = OpenAI(model="gpt-4o-mini")`로 잠깐 바꿔서 돌려보면 (Stage 5부터 준비된 진짜 크레딧 필요), "답변:" 뒤에 `{{answer}}`가 아니라 진짜 생성된 문장이 이어지는 걸 볼 수 있습니다. 그때는 템플릿에서 `{{answer}}`를 지우는 게 맞습니다 — 그 자리는 모델이 알아서 채우는 영역이라 미리 텍스트를 넣어둘 필요가 없습니다.