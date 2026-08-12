# Stage 1 — 전역 Settings

## 목표
Stage 0에서는 `Settings`를 건드리지 않고 기본값 그대로 썼습니다. 이번엔 `Settings.node_parser`(청크 분할 전략)를 직접 바꿔보고, 그 값이 **아무 인자로도 넘기지 않았는데** 인덱싱 결과에 자동 반영되는 걸 확인합니다.

비교 대상: [backend/app/llama_index_settings.py](../../backend/app/llama_index_settings.py)

## 배경 지식 (먼저 읽기)

```python
Settings.llm = OpenAI(...)
Settings.embed_model = OpenAIEmbedding(...)
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=10)
```

이 세 줄을 한 번 실행해두면, 이후 어디서 `VectorStoreIndex.from_documents(docs)`를 호출하든 `llm=`, `embed_model=`, `node_parser=`를 명시적으로 넘기지 않아도 이 값들이 자동으로 쓰입니다. 파이썬 전역 변수처럼 동작하는 싱글턴입니다.

## 할 일

`starter.py`의 TODO를 채우세요. 이번엔 크레딧 걱정 없이 `MockEmbedding`을 기본으로 씁니다 — 이번 스테이지의 관심사는 **답변 품질이 아니라 청크 개수**라서 임베딩이 진짜일 필요가 없습니다.

1. `Settings.transformations = [SentenceSplitter(chunk_size=256, chunk_overlap=20)]`로 설정
2. `lyft-2021-10k.pdf`를 로드해서 인덱스 생성 → `len(index.docstore.docs)`로 노드 개수 출력
3. `Settings.transformations`를 `chunk_size=1024, chunk_overlap=20`으로 바꿔서 같은 문서로 다시 인덱스 생성 → 노드 개수 다시 출력
4. 두 결과를 비교

## ⚠️ 실제로 겪게 될 함정: `Settings.node_parser`를 두 번째로 바꾸면 반영이 안 됩니다

직관적으로는 `Settings.node_parser = SentenceSplitter(chunk_size=1024, ...)`로 재할당하면 될 것 같지만, 실제로 해보면 **두 번째 인덱스도 첫 번째와 똑같은 노드 개수**가 나옵니다. LlamaIndex 0.12.23의 `Settings` 내부 구현 때문입니다:

```python
# llama_index/core/settings.py (_Settings 클래스)
@property
def transformations(self) -> List[TransformComponent]:
    if self._transformations is None:
        self._transformations = [self.node_parser]   # 최초 1회만 캐싱!
    return self._transformations
```

`VectorStoreIndex.from_documents()`는 `Settings.node_parser`가 아니라 `Settings.transformations`를 읽습니다. 그런데 `transformations`는 **최초로 접근되는 순간의 `node_parser`를 캐싱**해두고, 그 뒤로는 `node_parser`를 다시 바꿔도 캐싱된 옛날 값을 계속 돌려줍니다.

**해결책:** `Settings.node_parser` 대신 `Settings.transformations = [SentenceSplitter(...)]`를 직접 설정하면 매번 새 값이 반영됩니다. (`starter.py`도 이 방식으로 되어 있습니다.)

이건 위키/블로그에도 잘 안 나오는, 직접 실행해봐야만 만나는 종류의 함정입니다 — sec-insights는 `Settings.node_parser`를 **딱 한 번**만 설정하고 다시는 바꾸지 않기 때문에([llama_index_settings.py](../../backend/app/llama_index_settings.py)) 이 문제를 겪지 않습니다.

## 실행

```bash
cd study/stage1_settings
python starter.py
```

## 관찰 포인트

- `chunk_size`가 작을수록 노드 개수는 늘어나나요, 줄어드나요? 왜 그런지 한 문장으로 설명해보세요.
 : 줄어들어. 사이즈가 늘었으니까 큰 뭉탱이로 자르니까 개수가 줄얻르지
- `chunk_overlap`을 0으로 바꾸면 노드 개수가 어떻게 달라지나요? : 조금 많아져
- sec-insights는 `chunk_size=512, chunk_overlap=10`을 씁니다 ([constants.py](../../backend/app/chat/constants.py)). 왜 512 근처를 골랐을지 추측해보세요 (힌트: 너무 작으면 문맥이 끊기고, 너무 크면 검색 정확도가 떨어지고 비용이 늘어남).
 : 왤까? 몰라.
  - **답:** 트레이드오프의 중간 지점이라서. ① 너무 작으면(예: 128) 한 청크에 "매출은 X달러" 같은 문장의 앞뒤 맥락이 잘려서 검색은 되는데 답변 재료가 부실해짐. ② 너무 크면(예: 4096) 청크 하나에 서로 다른 주제가 섞여서 "가장 유사한 청크"를 뽑아도 그 안에 잡음이 많고, top_k개를 LLM에 넣을 때 토큰(=비용)도 커짐. 512는 OpenAI 임베딩/LLM 튜토리얼에서도 자주 쓰이는 관행적 기본값 — "이 정도면 문단 하나 분량은 담긴다"는 경험적 절충점입니다. (이건 공식 문서에 박힌 규칙이 아니라 **설계 해석**입니다 — 정답 chunk_size는 도메인/실험에 따라 다름)


## 체크포인트

- [x] `Settings`에 값을 한 번 세팅하면 이후 어디서 인덱스를 만들든 자동 적용된다는 걸 실행으로 확인했다
  - (버그 수정 전 결과였음 — `Settings.transformations` 방식으로 재실행하면 `761 / 209`가 나옵니다) : 확인함.
- [x] chunk_size와 노드 개수의 관계를 실행 결과 숫자로 설명할 수 있다
  - chunk_size가 커지면 청크 하나가 더 많은 텍스트를 담으므로 노드 개수는 줄어든다 (256→761개, 1024→209개).

다음: `study/stage2_storage_context`

## 질문
1. chunk_overlap 이 뭐지?
   - [x] **짧게:** 앞 청크의 끝부분을 다음 청크 앞부분에 그대로 복사해서 겹치게 만드는 토큰 수. `chunk_overlap=20`이면 청크N의 마지막 20토큰이 청크N+1의 첫 20토큰으로도 다시 들어감.
   - **왜 필요한가:** 안 겹치면 문장/문맥이 청크 경계에서 뚝 잘려서, 그 경계에 걸친 정보는 어느 청크를 검색해도 온전히 안 잡힘. 겹치게 하면 경계 부근 내용이 최소 한쪽 청크엔 통째로 들어가서 검색 누락을 줄임.
   - **트레이드오프:** overlap이 클수록 중복 저장되는 텍스트가 많아져 노드 수·임베딩 비용·저장공간이 늘어남. sec-insights는 512 중 10(2%)만 겹쳐서 최소한만 씀.
2. 새로 맡는 도메인에서 청크사이즈를 판단하는 기준은 실험밖에 없나? 베스트프랙티스는?
   - [x] **아니요, 실험 전에 좁혀주는 휴리스틱이 있습니다:**
     1. **도메인의 자연스러운 단위에 맞춘다** — 문단 단위 문서(법률/재무)는 문단 하나 분량, 코드는 함수/클래스 단위(LlamaIndex의 `CodeSplitter` 등 언어별 스플리터 사용), 표는 행이 안 잘리게.
     2. **임베딩 모델의 실용 구간을 기본값으로** — OpenAI 계열 임베딩은 대략 200~500토큰에서 잘 동작하고, 800~1000 넘어가면 검색 정밀도가 떨어지는 경향이 흔히 보고됨(**설계 해석**, 모델·도메인마다 다를 수 있음).
     3. **컨텍스트 예산 역산** — `similarity_top_k × chunk_size`가 시스템프롬프트/대화이력 빼고 LLM 컨텍스트 안에 여유있게 들어가는지 계산.
     4. **overlap은 chunk_size의 10~20%**를 시작값으로.
   - **결국 최종 검증은 실험입니다** — 위 휴리스틱으로 후보 2~3개(예: 256/512/1024)를 좁힌 뒤, 실제 Q&A 평가셋으로 검색 hit-rate·답변 정확도를 비교해서 확정하는 게 실무 관행입니다. "실험만이 유일한 방법"은 아니지만 "실험 없이 확정"도 아닙니다.