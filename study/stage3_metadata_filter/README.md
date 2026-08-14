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

- 필터 없이 검색했을 때 `source_nodes`에 lyft/uber가 섞여 나왔나요? 몇 대 몇으로 나왔나요?
  - 실행 결과: `필터 없음: {'uber': 5, 'lyft': 1}` (실행할 때마다 비율이 달라질 수 있음 — 아래 질문 2 참고)
- 필터를 걸었을 때 정말 uber 노드만 나왔나요?
  - 실행 결과: `uber 필터: {'uber': 6}` — 네, uber만 나왔습니다.
- 만약 sec-insights가 이 필터링을 안 했다면 어떤 문제가 생길지 한 문장으로 설명해보세요.
  - [x] **답:** 사용자가 대화창에서 Uber 문서만 선택했는데도, 벡터 검색이 전체(모든 유저의 모든 문서) 테이블에서 "의미상 가장 가까운" 청크를 가져오기 때문에 **엉뚱하게 Lyft(또는 다른 유저의 문서) 내용이 답변 근거로 섞여 들어갈 수 있습니다.** 최악의 경우 다른 회사 재무 수치를 Uber 수치인 것처럼 답변하게 됨 — 필터링은 "검색 대상을 사용자가 실제로 선택한 문서로만 좁히는" 격리 장치입니다.

## 체크포인트

- [x] 왜 문서별로 별도 인덱스(테이블)를 안 만들고 메타데이터 필터링을 쓰는지 설명할 수 있다
  - 문서마다 테이블을 새로 만들면 문서 수만큼 스키마/커넥션 관리가 늘어나고, "여러 문서를 동시에 검색"하는 것도 여러 테이블에 따로 질의해서 합쳐야 해서 번거롭습니다. 하나의 테이블 + 메타데이터 필터는 스키마 하나로 문서 수와 무관하게 확장되고, 검색 시 필터 조건만 바꾸면 되므로 훨씬 단순합니다.
- [x] `ExactMatchFilter`가 벡터 유사도 계산 *전*에 걸러내는지 *후*에 걸러내는지
  - **전입니다 (확인함, 더 이상 미검증 가설 아님).** 아래 질문 2의 답에서 실제 소스코드로 확인 — 필터로 후보 집합을 먼저 줄인 뒤 그 안에서만 유사도 랭킹을 계산합니다.

다음: `study/stage4_prompt_synth`

## 질문
1. `index = VectorStoreIndex.from_documents(lyft_docs + uber_docs)`에서 `+`가 어떻게 가능하지? - 할 수도 있나?
   - [x] `SimpleDirectoryReader().load_data()`는 LlamaIndex의 특별한 자료구조가 아니라 그냥 파이썬 **`list`**를 반환합니다 (`List[Document]`). `+`는 LlamaIndex와 무관한 **파이썬 리스트의 기본 연산자**(`list.__add__`) — 두 리스트를 이어붙여 새 리스트를 만드는 것뿐입니다. `lyft_docs + uber_docs`는 `[lyft의 Document, ..., uber의 Document, ...]` 형태의 합쳐진 리스트가 되고, `from_documents()`는 "Document 리스트 하나"만 받으면 되므로 문제없이 동작합니다.
2. stage3의 의도가 뭐지? 필터없으면 당연히 lyft랑 uber가 나오겠지. 둘다 넣었으니까. 근데 필터없을때 uber5개 lyft1개 나왔는데 왜 uber로 필터하니까 uber가 6개나오지?
   - [x] **Stage 3의 의도:** "여러 회사 문서를 한 테이블에 같이 넣으면 검색이 섞일 수 있다"는 문제와, "메타데이터 필터로 그 섞임을 원천 차단할 수 있다"는 해결책을 숫자로 직접 겪어보는 것입니다. 체크포인트에 답한 "왜 안 하면 문제가 생기는지"가 이 스테이지의 핵심 결론입니다.
   - **왜 5:1처럼 한쪽으로 쏠렸나 (실행할 때마다 바뀌는 이유):** `MockEmbedding` 소스를 보면 입력 텍스트와 무관하게 **항상 똑같은 벡터**(`[0.5, 0.5, ...]`)를 반환합니다. 그래서 lyft든 uber든 모든 청크의 유사도 점수가 정확히 동점(1.0)입니다. LlamaIndex의 top-k 선택 함수(`get_top_k_embeddings`)는 동점일 때 `heapq`로 `(점수, node_id)` 튜플을 비교해서 순위를 매기는데, `node_id`는 청크마다 **매번 새로 생성되는 랜덤 UUID**라서 어느 회사 청크가 "이긴다"는 사실상 랜덤입니다. 즉 5:1이라는 비율 자체는 **의미 있는 검색 결과가 아니라 Mock의 한계로 생긴 노이즈**입니다 (Stage 0 README에서 미리 경고했던 "Mock으로는 진짜 검색 품질을 판단할 수 없다"는 게 바로 이런 형태로 나타난 것).
   - **왜 필터하면 uber가 6개 다 나오나:** 필터는 유사도 계산 *전에* 후보 청크 집합을 먼저 "uber 태그가 붙은 청크들"로만 좁힙니다. lyft 청크는 애초에 순위 경쟁에 끼지도 못하고 제외되므로, 동점이든 아니든 top-6는 전부 uber 청크 중에서만 뽑힙니다. 필터링이 "유사도 순위 경쟁 자체를 특정 부분집합으로 제한한다"는 걸 이번 실행 결과가 정확히 보여준 셈입니다.
