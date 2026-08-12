# Stage 2 — StorageContext로 저장/재로딩

## 목표
Stage 0~1에서는 스크립트를 실행할 때마다 매번 처음부터 인덱스를 새로 만들었습니다 (임베딩 API를 매번 다시 호출). 실제 서비스에서는 이러면 안 됩니다 — sec-insights도 이미 인덱싱된 문서는 다시 임베딩하지 않고 저장된 걸 불러옵니다.

비교 대상: [engine.py:124-171](../../backend/app/chat/engine.py) `build_doc_id_to_index_map()`의 load-or-build 분기

## 배경 지식

- `index.storage_context.persist(persist_dir="...")` — 인덱스의 docstore/index_store/vector_store 내용을 디스크(json 파일들)에 저장
- `StorageContext.from_defaults(persist_dir="...")` — 저장된 파일에서 StorageContext를 복원
- `load_index_from_storage(storage_context)` — 복원된 StorageContext로부터 인덱스 객체를 재생성 (이 과정에서 임베딩 API 호출이 전혀 없음 — 이미 계산된 벡터를 그대로 읽어올 뿐)

## 할 일

`starter.py`의 TODO를 채우세요. 임베딩 호출 횟수를 세는 카운터가 이미 준비되어 있습니다 (`CountingMockEmbedding`) — 크레딧 걱정 없이 "재로딩할 때 진짜로 임베딩을 다시 안 하는지"를 숫자로 확인할 수 있습니다.

1. `lyft-2021-10k.pdf` 로드 → 인덱스 생성 (1차: 새로 생성)
2. `index.storage_context.persist(persist_dir="./storage")`로 저장
3. **같은 프로세스 안에서** `StorageContext.from_defaults(persist_dir="./storage")` + `load_index_from_storage(...)`로 재로딩
4. 1차 생성 시 임베딩 호출 횟수와 2차 재로딩 시 임베딩 호출 횟수를 비교 출력

## 실행

```bash
cd study/stage2_storage_context
python starter.py
```

두 번째로 실행하면(`./storage` 폴더가 이미 있는 상태) 어떻게 되는지도 관찰해보세요 — `from_defaults(persist_dir=...)`가 기존 파일을 또 읽어들이는지, 아니면 매번 덮어쓰는지 확인.

## 관찰 포인트

- 1차 생성 시 임베딩 호출 횟수: 노드 개수와 같나요? (MockEmbedding은 노드 하나당 몇 번 호출되는지 배치 크기에 따라 다를 수 있습니다 — 정확한 숫자보다 "0이 아니다 vs 0이다"가 중요)
- 2차 재로딩 시 임베딩 호출 횟수: 0이어야 정상입니다. 0이 아니라면 왜 그런지 코드를 다시 보세요.
- `./storage` 폴더 안에 어떤 파일들이 생겼는지 `ls`로 확인해보세요 (`docstore.json`, `index_store.json`, `default__vector_store.json` 등)

## sec-insights와의 차이

sec-insights는 로컬 디스크가 아니라 **S3**에 저장합니다 (`fs=s3_fs` 파라미터, [engine.py:59-67](../../backend/app/chat/engine.py)). `StorageContext.from_defaults(fs=...)`처럼 `fs` 인자에 `fsspec` 파일시스템 객체를 넘기면 로컬 디스크 대신 S3/GCS 등 어디든 저장할 수 있습니다 — 이번 스테이지의 `persist_dir` 로직 자체는 동일하고 `fs`만 바뀝니다.

## 체크포인트

- [x] "인덱스를 만든다"와 "인덱스를 저장한다"가 별개의 단계라는 걸 설명할 수 있다
- [x] 재로딩 시 임베딩 API가 호출되지 않는 이유를 설명할 수 있다

**실행 결과 (검증 완료):**
```
[1차 생성]   노드 개수: 367, 임베딩 호출 횟수: 734
[2차 재로딩] 노드 개수: 367, 임베딩 호출 횟수: 0
```
노드 개수는 동일하게 유지되고, 재로딩 시 임베딩 호출은 정확히 0회 — `load_index_from_storage()`가 디스크에 저장된 벡터를 그대로 읽기만 하고 재계산하지 않음을 숫자로 확인했습니다.

다음: `study/stage3_metadata_filter`
