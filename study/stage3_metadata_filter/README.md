# Stage 3 — 문서 여러 개를 한 인덱스에 넣고 필터링

## 목표
sec-insights는 문서마다 별도 벡터DB 테이블을 만들지 않습니다. **모든 문서의 청크를 하나의 Postgres 테이블에 같이 저장**하고, 검색할 때 메타데이터로 "이 문서에서만 찾아라"라고 걸러냅니다. 왜 이렇게 하는지, 안 하면 어떤 문제가 생기는지 직접 겪어봅니다.

비교 대상: [engine.py:103-108](../../backend/app/chat/engine.py) `index_to_query_engine()`

## ⚠️ 실제로 겪게 될 함정: 메타데이터 키로 `"doc_id"`를 쓰면 안 됩니다

직관적으로 문서 구분용 메타데이터 키 이름을 `"doc_id"`라고 짓고 싶어지는데, 이러면 **필터가 항상 0건을 반환**합니다. 직접 재현해서 원인을 확인했습니다.

LlamaIndex는 청크(Node)를 만들 때 내부적으로 `node.metadata["doc_id"]`에 **원본 Document의 UUID**를 자동으로 채워 넣습니다 (`ref_doc_id`, `document_id`와 함께 예약된 키). 그래서 우리가 `doc.metadata["doc_id"] = "uber"`라고 넣어도, 인덱싱 과정에서 LlamaIndex가 같은 키를 자기 값(UUID)으로 덮어써버립니다. 실제로 찍어보면:

```python
>>> index.vector_store.data.metadata_dict[node_id]
{'page_label': '1', ..., 'doc_id': 'f5b61c3e-7619-4b4f-9986-2fad546ad343', ...}
```

`"uber"`가 아니라 UUID가 들어있죠. 그래서 `ExactMatchFilter(key="doc_id", value="uber")`는 절대 매치되지 않습니다.

**해결책:** 예약되지 않은 키 이름을 씁니다. 이 스테이지는 sec-insights와 똑같이 `"db_document_id"`를 씁니다 — [constants.py](../../backend/app/chat/constants.py)의 `DB_DOC_ID_KEY = "db_document_id"`가 **정확히 이 충돌을 피하려고** 지어진 이름이었다는 걸 이제 알 수 있습니다. 처음 읽었을 땐 그냥 임의의 상수처럼 보였는데, 직접 겪어보니 왜 이 이름이어야만 했는지 이해가 됩니다.

## 할 일

`starter.py`의 TODO를 채우세요. (키 이름은 이미 `DOC_ID_KEY = "db_document_id"`로 준비되어 있습니다)

1. `lyft-2021-10k.pdf`와 `uber-2021-10k.pdf`를 각각 로드하되, 각 Document의 `metadata[DOC_ID_KEY]`에 `"lyft"` / `"uber"`를 채워넣기
2. 두 문서 리스트를 합쳐서 **하나의** `VectorStoreIndex.from_documents(all_docs)` 생성
3. **필터 없이** `index.as_query_engine(similarity_top_k=6)`로 아무 질문이나 검색 → `response.source_nodes`의 `DOC_ID_KEY` 메타데이터를 출력해서 lyft/uber가 섞여 나오는지 확인
4. `MetadataFilters(filters=[ExactMatchFilter(key=DOC_ID_KEY, value="uber")])`를 걸어서 같은 질문 재검색 → 이번엔 uber만 나오는지 확인

## 실행

```bash
cd study/stage3_metadata_filter
python starter.py
```

이번에도 `MockEmbedding`을 씁니다. Mock은 모든 텍스트를 거의 같은 벡터로 취급하므로 "의미적으로 진짜 관련있는 청크가 뽑히는지"는 볼 수 없지만, **필터가 doc_id 기준으로 결과 집합 자체를 걸러내는지**는 완벽하게 확인 가능합니다 (필터링은 벡터 유사도와 무관하게 메타데이터로 동작하는 별개 로직이라서).

## 관찰 포인트

- 필터 없이 검색했을 때 `source_nodes`에 lyft/uber가 섞여 나왔나요? 몇 대 몇으로 나왔나요? (검증 결과: `{'lyft': 3, 'uber': 3}`)
- 필터를 걸었을 때 정말 uber 노드만 나왔나요? (검증 결과: `{'uber': 6}`)
- 만약 sec-insights가 이 필터링을 안 했다면 어떤 문제가 생길지 한 문장으로 설명해보세요. (힌트: 사용자가 Uber 문서만 선택해서 질문했는데 Lyft 내용이 답변에 섞여 나온다면?)

## 체크포인트

- [ ] 왜 문서별로 별도 인덱스(테이블)를 안 만들고 메타데이터 필터링을 쓰는지 설명할 수 있다
- [ ] `ExactMatchFilter`가 벡터 유사도 계산 *전*에 걸러내는지 *후*에 걸러내는지 궁금증이 생겼다면 다음 검증 후보로 남겨두세요 (LlamaIndex 벡터 스토어 구현체마다 다를 수 있습니다 — 미검증 가설)

다음: `study/stage4_prompt_synth`
