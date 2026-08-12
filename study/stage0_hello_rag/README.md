# Stage 0 — Hello RAG

## 목표
LlamaIndex가 "PDF → 질문에 답하기"까지 대신 해주는 걸 최소 코드로 직접 겪어봅니다.
아직 `Settings` 커스터마이징, 저장/재로딩, 필터링 같은 건 신경 쓰지 마세요 — 딱 4줄짜리 핵심 흐름만 봅니다.

## 할 일

`starter.py`를 열어서 `TODO` 표시된 부분만 채우세요.

1. `SimpleDirectoryReader`로 `frontend/public/lyft-2021-10k.pdf` 하나만 읽기
   - 힌트: `SimpleDirectoryReader(input_files=[path])`
2. `VectorStoreIndex.from_documents(documents)`로 인덱스 만들기
3. `index.as_query_engine()`으로 쿼리 엔진 만들기
4. `query_engine.query("이 문서는 어느 회사에 대한 문서야?")` 실행하고 결과 출력

## 실행

```bash
cd study/stage0_hello_rag
python starter.py
```

## 관찰 포인트 (실행하면서 꼭 확인)

- 실행 시간이 얼마나 걸리나요? (PDF 파싱 + 임베딩 API 호출이 여기서 다 일어납니다) credit없어....예시로 써줘그냥...
- `documents`를 `print(len(documents))` 해보면 페이지 수만큼 Document가 나오나요? 137개
- 질문을 문서와 전혀 관련 없는 걸로 바꿔보면 ("오늘 날씨 어때?") 어떤 답이 나오나요? credit없어....예시로 써줘그냥...
  - 이게 나중에 Stage 5~7에서 "에이전트가 도구를 선택해야 하는 이유"로 이어집니다.

## 크레딧 없이 테스트하기

OpenAI 크레딧이 없으면 `run_with_mock.py`를 실행하세요. API 키 없이도 됩니다.

```bash
python run_with_mock.py
```

`MockEmbedding`/`MockLLM`으로 실제 API 호출 없이 인덱싱→검색→합성 파이프라인 전체가 도는지 확인합니다.
`Node 개수`(청크가 몇 개 만들어졌는지), `source_nodes`(어떤 청크가 검색됐는지)는 실제와 동일하게 확인 가능합니다.

**주의:** `MockEmbedding`은 입력 텍스트와 무관하게 항상 비슷한 벡터를 반환하므로 `score=1.0000`처럼 모든 청크의 유사도가 똑같이 나옵니다. 즉 **"어떤 청크가 진짜 질문과 의미적으로 가까운지"는 이 mock 결과로 판단할 수 없습니다** — top-k 선택 로직이 실제로 도는지, Node 개수가 맞는지 같은 "배관(plumbing)"만 검증하는 용도입니다. 실제 검색 품질은 크레딧을 채워 `starter.py`로 확인하세요.

또한 답변 출력에서 `Answer:` 앞의 프롬프트 전문이 그대로 보이는데, 이게 바로 LlamaIndex 기본 `text_qa_template`입니다 — Stage 4에서 이 템플릿을 직접 커스터마이징하게 됩니다 (sec-insights의 `qa_response_synth.py`가 하는 일과 동일).

## 막히면

- `openai.AuthenticationError` → `study/.env`에 `OPENAI_API_KEY` 확인
- `ModuleNotFoundError` → `pip install -r study/requirements.txt` 다시 실행했는지 확인
- 그래도 안 되면 `solution.py`를 열어 비교하세요.

## 체크포인트

이 스테이지를 마쳤다면:
- [x] `Document`와 `Node`(청크)의 차이를 한 문장으로 설명할 수 있다
    - Document는 원문 문서. node는 Document를 자른 것.
- [x] `VectorStoreIndex.from_documents()` 한 줄이 내부적으로 하는 일 3가지를 말할 수 있다 (청크 분할 / 임베딩 / 저장)
    - 청킹, 임베딩, 메모리에 객체로 저장.

다음: `study/stage1_settings`

## 질문
- 뒤의 학습에서 답변할 수 있으면 넘길것.

1. 쿼리 엔진을 돌리면 VectorStoreIndex.from_documents -> 인덱스를만들고 -> query engine(어떤 알고리즘으로 검색할지)로 search하는거야?
   - [x] **맞음.** 인덱싱(청킹+임베딩+저장)은 `from_documents`에서 끝. `as_query_engine()`은 검색 알고리즘을 "결정"만 하고, `.query()`가 실제 검색+답변합성을 "실행".
2. VectorStoreIndex.from_documents 가 반환하는 index는 무슨 정보가 들어있어? 인덱스 전체를 반환해?
   - [x] 데이터 원본이 아니라 **핸들**. `docstore`(원문 청크) · `index_struct`(노드ID 목록) · `storage_context.vector_store`(임베딩)를 가리키는 포인터 묶음. 디스크 저장은 별도(`persist()`) 필요.
3. query engine에 알고리즘을 선택할 수 있어?
   - [x] **가능.** `as_query_engine(similarity_top_k=, response_mode=)`로 조절하거나, `VectorIndexRetriever` + `RetrieverQueryEngine`으로 완전 교체 가능.
