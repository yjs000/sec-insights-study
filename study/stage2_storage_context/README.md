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

- 1차 생성 시 임베딩 호출 횟수: 노드 개수와 같나요? (MockEmbedding은 노드 하나당 몇 번 호출되는지 배치 크기에 따라 다를 수 있습니다 — 정확한 숫자보다 "0이 아니다 vs 0이다"가 중요) : 두번쨰는 임베딩 호출횟수가 0
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

## 질문
1. 2차 : 재로딩 왜해? starter.py 59line
   - [x] 실제 서비스에서 임베딩 계산은 비용·시간이 듭니다(API 호출). 그래서 "한 번만 계산해서 저장(persist)해두고, 그 다음부터는 계속 그 저장본을 불러 쓴다"가 정상 운영 방식입니다. 59번 줄의 "2차: 재로딩"은 **"서버가 재시작됐거나 새 요청이 들어온 상황"을 같은 스크립트 안에서 흉내낸 것** — 실제로는 다른 프로세스(예: 다음 날 다시 켠 서버)에서 일어날 일입니다. sec-insights의 `build_doc_id_to_index_map()`([engine.py](../../backend/app/chat/engine.py))이 매 채팅 요청마다 이 "이미 있으면 로드, 없으면 생성" 분기를 탑니다.
2. `index.storage_context.persist(...)`, `StorageContext.from_defaults(...)`, `load_index_from_storage(...)`가 반환하는 것은?
   - [x] `index.storage_context.persist(persist_dir=...)` → **반환값 없음(`None`)**. 디스크에 `docstore.json`/`index_store.json`/`default__vector_store.json` 파일을 쓰는 게 전부인 부수효과(side-effect) 함수.
   - `StorageContext.from_defaults(persist_dir=...)` → **`StorageContext` 객체**. 저장된 3개 json 파일을 읽어서 메모리 위에 docstore/index_store/vector_store를 복원한 것. 아직 "인덱스"는 아니고 재료들의 묶음.
   - `load_index_from_storage(storage_context)` → **`VectorStoreIndex` 객체**. `storage_context` 안의 `index_store`(어떤 노드들로 구성된 인덱스인지)를 읽어서, 실제로 질의(`as_query_engine()`)할 수 있는 완성된 인덱스 객체로 조립.
3. `./storage` 위치는?
   - [x] `starter.py`의 `PERSIST_DIR = Path(__file__).resolve().parent / "storage"`로 정의되어 있어서, **어디서 스크립트를 실행하든** 항상 `study/stage2_storage_context/storage` 폴더를 가리킵니다 (README의 `./storage` 표기는 개념 설명용이고, 실제 코드는 실행 위치(cwd)에 의존하지 않도록 `__file__` 기준 절대경로를 씁니다).
4. S3, GCS가 뭐야?
   - [x] **S3**(Amazon Simple Storage Service)와 **GCS**(Google Cloud Storage)는 클라우드 "객체 스토리지"입니다. 폴더/파일 구조를 흉내낸 API로 어디서든(여러 서버 인스턴스에서도) 같은 파일에 접근할 수 있게 해주는 저장소 — 로컬 디스크는 그 서버가 꺼지거나 다른 서버로 요청이 가면 접근 불가능하지만, S3/GCS는 네트워크로 붙는 공유 저장소라 서버가 몇 대든 같은 인덱스를 공유할 수 있습니다. sec-insights가 로컬 디스크 대신 S3를 쓰는 이유([engine.py](../../backend/app/chat/engine.py) `fs=s3_fs`)가 바로 이것입니다.
5. 인덱스가 뭐야?
   - [x] 일반적 의미: "전부 훑어보지 않고 빠르게 찾기 위한 자료구조"(책의 색인처럼). `VectorStoreIndex`는 구체적으로 **"텍스트 청크 ↔ 임베딩 벡터 ↔ 메타데이터"를 연결해두고, 질문이 들어오면 그 벡터공간에서 가장 가까운 청크들을 빠르게 찾아주는 자료구조**입니다. Stage 0 질문2에서 다룬 것처럼 `index` 객체 자체는 데이터가 아니라 `docstore`/`index_struct`/`vector_store`를 가리키는 핸들이라는 것도 같이 기억해두세요.
6. 재로딩 시 임베딩 API가 호출되지 않는 이유가 뭐야?
   - [x] `persist()` 시점에 이미 계산된 임베딩 벡터들이 `default__vector_store.json`에 **숫자 그대로 저장**돼 있습니다. `load_index_from_storage()`는 이 파일을 읽어서 그 숫자들을 메모리에 그대로 올리는 것뿐이라, "텍스트 → 벡터로 다시 변환"하는 임베딩 모델 호출 자체가 필요 없습니다. (이번 스테이지에서 `CountingMockEmbedding`으로 직접 숫자로 확인한 부분 — 1차 734회, 2차 0회)