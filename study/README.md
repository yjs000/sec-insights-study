# LlamaIndex 학습 — 손으로 재현하기

`sec-insights`가 하는 일을 스테이지별로 아주 작은 스크립트로 직접 재현합니다.
각 스테이지 폴더에는:

- `README.md` — 이번 스테이지의 목표, 할 일, 힌트, 체크포인트
- `starter.py` — 직접 채워 넣을 스켈레톤 (TODO 표시된 부분만 작성하면 됨)
- `solution.py` — 막혔을 때만 보는 참고 답안 (먼저 직접 시도한 뒤에 열어볼 것)

## 준비물

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r study/requirements.txt
```

`study/.env.example`을 복사해서 `study/.env`를 만들고 값을 채워넣으세요.

```bash
cp study/.env.example study/.env
```

- Stage 0~4: `OPENAI_API_KEY`만 있으면 되고, 대부분 `MockEmbedding`/`MockLLM`으로 크레딧 없이 진행 가능합니다. 위 `pip install -r study/requirements.txt`로 충분합니다.
- Stage 5~9: 실제 LLM이 필요합니다. `study/llm_provider.py`가 `LLM_PROVIDER` 값(`nvidia` 추천/무료, 또는 `openai`)에 따라 LLM/임베딩을 골라줍니다. NVIDIA 키는 [build.nvidia.com](https://build.nvidia.com)에서 무료로 발급받을 수 있습니다.
  - **Stage 5로 넘어가기 전에 패키지를 한 번 더 업그레이드해야 합니다** (`requirements.txt`의 기본 설치만으로는 부족합니다 — NVIDIA 연동 패키지가 `llama-index-core>=0.13`을 요구해서 별도로 올려야 함):
    ```bash
    pip install "llama-index-core>=0.13,<0.15" "pandas>=2.3.3" llama-index-readers-file llama-index-embeddings-openai llama-index-llms-openai llama-index-llms-nvidia llama-index-embeddings-nvidia python-dotenv
    pip uninstall -y llama-index-agent-openai llama-index-program-openai llama-index-question-gen-openai
    ```
  - 이 업그레이드 이후 `OpenAIAgent` 대신 provider 무관한 `FunctionAgent`를 씁니다 — 자세한 이유는 각 스테이지 README의 "API 변경" 절 참고.
  - (Python 3.14를 쓴다면 `pandas`가 소스 빌드를 시도하다 실패할 수 있어 `pandas>=2.3.3`으로 버전을 명시해 wheel이 있는 버전을 강제합니다.)

테스트용 PDF는 리포지토리에 이미 있는 걸 그대로 씁니다:
`frontend/public/lyft-2021-10k.pdf`, `frontend/public/uber-2021-10k.pdf`

## 스테이지 목록

| # | 폴더 | 배우는 것 | 비교할 실제 코드 |
|---|---|---|---|
| 0 | `stage0_hello_rag` | 문서 로드 → 인덱스 → 질의 최소 흐름 | `backend/app/chat/engine.py` |
| 1 | `stage1_settings` | 전역 `Settings` (LLM/임베딩/청크) | `backend/app/llama_index_settings.py` |
| 2 | `stage2_storage_context` | 인덱스 저장/재로딩 | `engine.py: build_doc_id_to_index_map()` |
| 3 | `stage3_metadata_filter` | 문서 여러 개를 한 인덱스에 + 필터링 | `engine.py: index_to_query_engine()` |
| 4 | `stage4_prompt_synth` | 답변 합성 프롬프트 커스터마이징 | `qa_response_synth.py` |
| 5 | `stage5_sub_question` | QueryEngineTool + SubQuestionQueryEngine | `engine.py` 230행대 |
| 6 | `stage6_function_tool` | 파이썬 함수를 도구로 (FunctionTool) | `tools.py` |
| 7 | `stage7_agent_of_agents` | 도구의 계층적 조합 (에이전트를 도구로) | `engine.py` 250~301행 |
| 8 | `stage8_streaming_callback` | 스트리밍 응답 + 콜백 이벤트 | `messaging.py` |
| 9 | `stage9_mini_fastapi` (선택) | SSE 엔드포인트로 묶기 | `conversation.py` |

각 스테이지를 마치면 저한테 코드를 보여주세요 — 리뷰하고 다음 스테이지로 넘어가겠습니다.
진행하면서 이해가 바뀐 부분이나 막혔던 부분은 `/wiki-study-log`로 따로 기록할 수 있습니다.

## 지금 시작하기

```bash
cd study/stage0_hello_rag
cat README.md
```
