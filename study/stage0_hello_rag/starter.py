"""
Stage 0 — Hello RAG
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex

PDF_PATH = Path(__file__).resolve().parents[2] / "frontend" / "public" / "lyft-2021-10k.pdf"


def main():
    assert os.environ.get("OPENAI_API_KEY"), "study/.env에 OPENAI_API_KEY를 채워주세요"
    assert PDF_PATH.exists(), f"PDF를 찾을 수 없습니다: {PDF_PATH}"

    start = time.time()

    # TODO 1: SimpleDirectoryReader로 PDF_PATH 하나만 읽어서 documents 리스트 만들기
    documents = SimpleDirectoryReader(input_files=[str(PDF_PATH)]).load_data()  # <- 여기를 채우세요

    print(f"로드된 Document 개수: {len(documents)}")

    # TODO 2: VectorStoreIndex.from_documents(documents)로 인덱스 생성
    index = VectorStoreIndex.from_documents(documents)  # <- 여기를 채우세요

    # TODO 3: index.as_query_engine()으로 쿼리 엔진 생성
    query_engine = index.as_query_engine()  # <- 여기를 채우세요

    # TODO 4: 질문 실행
    question = "이 문서는 어느 회사에 대한 문서야?"
    response = query_engine.query(question)  # <- query_engine.query(question)

    print("\n질문:", question)
    print("답변:", response)
    print(f"\n걸린 시간: {time.time() - start:.1f}초")


if __name__ == "__main__":
    main()
