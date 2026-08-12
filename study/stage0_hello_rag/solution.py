"""
Stage 0 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
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

    documents = SimpleDirectoryReader(input_files=[str(PDF_PATH)]).load_data()
    print(f"로드된 Document 개수: {len(documents)}")

    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()

    question = "이 문서는 어느 회사에 대한 문서야?"
    response = query_engine.query(question)

    print("\n질문:", question)
    print("답변:", response)
    print(f"\n걸린 시간: {time.time() - start:.1f}초")


if __name__ == "__main__":
    main()
