"""
Stage 0 — 크레딧 없이 파이프라인만 검증하는 버전.

MockEmbedding / MockLLM은 진짜 OpenAI API를 부르지 않고 정해진 규칙으로
가짜 벡터/가짜 답변만 돌려줍니다. 그래서:
  - 답변 내용(response 텍스트)은 의미 없는 더미입니다.
  - 하지만 "청크가 몇 개 만들어졌는지", "검색이 top-k개를 잘 가져오는지",
    "에러 없이 인덱싱→검색→합성 파이프라인이 도는지"는 100% 실제와 동일하게 확인됩니다.

OpenAI API 키가 전혀 없어도 실행됩니다.
"""
import sys
import time
from pathlib import Path

# Windows 콘솔 기본 인코딩(cp949)이 PDF 안의 특수문자(•, — 등)를 못 찍어서 죽는 걸 방지
sys.stdout.reconfigure(encoding="utf-8")

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM

PDF_PATH = Path(__file__).resolve().parents[2] / "frontend" / "public" / "lyft-2021-10k.pdf"


def main():
    assert PDF_PATH.exists(), f"PDF를 찾을 수 없습니다: {PDF_PATH}"

    # 실제 OpenAIEmbedding/OpenAI 대신 가짜 모델을 전역 Settings에 등록.
    # embed_dim=1536은 text-embedding-3-small의 실제 차원수와 맞춰서
    # 나중에 실제 모델로 바꿀 때 구조가 달라지지 않게 함.
    Settings.embed_model = MockEmbedding(embed_dim=1536)
    Settings.llm = MockLLM()

    start = time.time()

    documents = SimpleDirectoryReader(input_files=[str(PDF_PATH)]).load_data()
    print(f"로드된 Document 개수: {len(documents)}")

    index = VectorStoreIndex.from_documents(documents)
    print(f"생성된 Node(청크) 개수: {len(index.docstore.docs)}")

    query_engine = index.as_query_engine(similarity_top_k=3)
    response = query_engine.query("이 문서는 어느 회사에 대한 문서야?")

    # 실제로 top-k=3개의 청크가 검색되어 답변 합성에 쓰였는지 확인
    print(f"\n검색되어 답변에 쓰인 소스 노드 개수: {len(response.source_nodes)}")
    for i, node in enumerate(response.source_nodes):
        preview = node.node.get_content()[:60].replace("\n", " ")
        print(f"  [{i}] score={node.score:.4f}  \"{preview}...\"")

    print("\n답변 (Mock LLM이라 의미 없는 더미 텍스트):")
    print(response)

    print(f"\n걸린 시간: {time.time() - start:.1f}초 (API 호출 없음)")


if __name__ == "__main__":
    main()
