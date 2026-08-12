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
- sec-insights의 [qa_response_synth.py](../../backend/app/chat/qa_response_synth.py)를 다시 보면, `doc_titles`는 파이썬 f-string으로 **지금** 채워지고 `{{context_str}}`(이중 중괄호)는 **나중에** LlamaIndex가 채운다는 걸 구분할 수 있나요?

## 체크포인트

- [ ] `text_qa_template`과 `refine_template`의 역할 차이를 설명할 수 있다
- [ ] 커스텀 프롬프트가 실제로 LLM에 어떻게 전달되는지 출력으로 확인했다

다음: `study/stage5_sub_question` — 여기부터는 실제 OpenAI 크레딧이 필요합니다 (MockLLM으로는 구조적 출력이 필요한 기능을 테스트할 수 없습니다).
