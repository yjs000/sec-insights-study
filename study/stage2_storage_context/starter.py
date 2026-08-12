"""
Stage 2 — StorageContext로 저장/재로딩
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
"""
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import MockEmbedding

PDF_PATH = Path(__file__).resolve().parents[2] / "frontend" / "public" / "lyft-2021-10k.pdf"
PERSIST_DIR = Path(__file__).resolve().parent / "storage"


class CountingMockEmbedding(MockEmbedding):
    """MockEmbedding과 동작은 같지만, 실제로 임베딩 함수가 몇 번 호출됐는지 셉니다."""
    call_count: int = 0

    def _get_text_embedding(self, text: str):
        type(self).call_count += 1
        return super()._get_text_embedding(text)

    def _get_text_embeddings(self, texts):
        type(self).call_count += len(texts)
        return super()._get_text_embeddings(texts)


def main():
    assert PDF_PATH.exists(), f"PDF를 찾을 수 없습니다: {PDF_PATH}"

    # 매번 깨끗하게 테스트하기 위해 이전 storage 폴더 삭제
    if PERSIST_DIR.exists():
        shutil.rmtree(PERSIST_DIR)

    Settings.embed_model = CountingMockEmbedding(embed_dim=1536)
    Settings.transformations = [SentenceSplitter(chunk_size=512, chunk_overlap=10)]

    documents = SimpleDirectoryReader(input_files=[str(PDF_PATH)]).load_data()

    # ---- 1차: 새로 생성 ----
    CountingMockEmbedding.call_count = 0
    index = VectorStoreIndex.from_documents(documents)
    print(f"[1차 생성] 노드 개수: {len(index.docstore.docs)}, 임베딩 호출 횟수: {CountingMockEmbedding.call_count}")

    # TODO 1: index.storage_context.persist(persist_dir=str(PERSIST_DIR))로 저장
    # 여기를 채우세요

    # ---- 2차: 재로딩 ----
    CountingMockEmbedding.call_count = 0

    # TODO 2: StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))로 storage_context 복원
    storage_context = None  # <- 여기를 채우세요

    # TODO 3: load_index_from_storage(storage_context)로 인덱스 재생성
    reloaded_index = None  # <- 여기를 채우세요

    print(f"[2차 재로딩] 노드 개수: {len(reloaded_index.docstore.docs)}, 임베딩 호출 횟수: {CountingMockEmbedding.call_count}")

    assert len(index.docstore.docs) == len(reloaded_index.docstore.docs), "노드 개수가 달라짐!"
    print("\n✅ 노드 개수는 동일하고, 재로딩 시 임베딩 호출은 0이어야 정상입니다.")


if __name__ == "__main__":
    main()
