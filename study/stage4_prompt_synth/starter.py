"""
Stage 4 — 답변 합성 프롬프트 커스터마이징
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.prompts.prompts import QuestionAnswerPrompt
from llama_index.core.prompts.prompt_type import PromptType
from llama_index.core.response_synthesizers.factory import get_response_synthesizer

PDF_PATH = Path(__file__).resolve().parents[2] / "frontend" / "public" / "lyft-2021-10k.pdf"


def main():
    Settings.embed_model = MockEmbedding(embed_dim=1536)
    Settings.llm = MockLLM()
    Settings.transformations = [SentenceSplitter(chunk_size=512, chunk_overlap=10)]

    documents = SimpleDirectoryReader(input_files=[str(PDF_PATH)]).load_data()
    index = VectorStoreIndex.from_documents(documents)

    question = "What was the total revenue?"

    # ---- 1) 기본 템플릿 ----
    default_engine = index.as_query_engine(similarity_top_k=1)
    default_response = default_engine.query(question)
    print("=" * 20, "기본 템플릿", "=" * 20)
    print(default_response)

    # ---- 2) 커스텀 템플릿 ----
    # TODO 1: {context_str}, {query_str} 자리표시자를 포함한 커스텀 QA 템플릿 문자열 작성
    #         "너는 SEC 재무제표 전문 애널리스트다. 반드시 문서에 나온 숫자를 인용해서 답하라" 같은 지시문 포함
    custom_qa_template_str = None  # <- 여기를 채우세요 (f-string 아님, 그냥 문자열)

    # TODO 2: QuestionAnswerPrompt(template=..., prompt_type=PromptType.QUESTION_ANSWER)로 프롬프트 객체 생성
    custom_qa_prompt = None  # <- 여기를 채우세요

    # TODO 3: get_response_synthesizer(text_qa_template=custom_qa_prompt)로 synthesizer 생성
    custom_synth = None  # <- 여기를 채우세요

    # TODO 4: index.as_query_engine(response_synthesizer=custom_synth, similarity_top_k=1)로 재질의
    custom_engine = None  # <- 여기를 채우세요
    custom_response = None  # <- custom_engine.query(question)

    print("\n" + "=" * 20, "커스텀 템플릿", "=" * 20)
    print(custom_response)


if __name__ == "__main__":
    main()
