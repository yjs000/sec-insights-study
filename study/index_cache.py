"""
문서 인덱스 캐싱 헬퍼 — Stage 2에서 배운 persist/reload 패턴을 재사용합니다.

Stage 5부터는 실제 임베딩 API(NVIDIA NIM 또는 OpenAI)를 쓰므로, 스크립트를
다시 실행할 때마다 같은 문서를 처음부터 재임베딩하면 시간과 크레딧이 낭비됩니다.
이 헬퍼는 각 스테이지 폴더 아래 ./storage에 인덱스를 저장해두고, 다음 실행부터는
그걸 그대로 불러옵니다.
"""
from pathlib import Path
from typing import List

from llama_index.core import (
    Document,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)


def get_or_build_index(documents: List[Document], persist_dir: str) -> VectorStoreIndex:
    """persist_dir에 캐시된 인덱스가 있으면 불러오고(임베딩 API 호출 없음),
    없으면 documents로 새로 만들어서 저장한다."""
    persist_path = Path(persist_dir)

    if persist_path.exists():
        try:
            storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
            print(f"[index_cache] 캐시된 인덱스를 불러옵니다: {persist_dir}")
            return load_index_from_storage(storage_context)
        except Exception as e:
            print(f"[index_cache] 캐시 로드 실패({e!r}), 새로 생성합니다.")

    print(f"[index_cache] 새 인덱스를 생성합니다 (임베딩 API 호출 발생): {persist_dir}")
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=persist_dir)
    return index
