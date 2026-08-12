"""
Stage 2 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
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
    call_count: int = 0

    def _get_text_embedding(self, text: str):
        type(self).call_count += 1
        return super()._get_text_embedding(text)

    def _get_text_embeddings(self, texts):
        type(self).call_count += len(texts)
        return super()._get_text_embeddings(texts)


def main():
    assert PDF_PATH.exists(), f"PDF를 찾을 수 없습니다: {PDF_PATH}"

    if PERSIST_DIR.exists():
        shutil.rmtree(PERSIST_DIR)

    Settings.embed_model = CountingMockEmbedding(embed_dim=1536)
    Settings.transformations = [SentenceSplitter(chunk_size=512, chunk_overlap=10)]

    documents = SimpleDirectoryReader(input_files=[str(PDF_PATH)]).load_data()

    CountingMockEmbedding.call_count = 0
    index = VectorStoreIndex.from_documents(documents)
    print(f"[1차 생성] 노드 개수: {len(index.docstore.docs)}, 임베딩 호출 횟수: {CountingMockEmbedding.call_count}")

    index.storage_context.persist(persist_dir=str(PERSIST_DIR))

    CountingMockEmbedding.call_count = 0
    storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
    reloaded_index = load_index_from_storage(storage_context)

    print(f"[2차 재로딩] 노드 개수: {len(reloaded_index.docstore.docs)}, 임베딩 호출 횟수: {CountingMockEmbedding.call_count}")

    assert len(index.docstore.docs) == len(reloaded_index.docstore.docs), "노드 개수가 달라짐!"
    print("\n✅ 노드 개수는 동일하고, 재로딩 시 임베딩 호출은 0이어야 정상입니다.")


if __name__ == "__main__":
    main()
