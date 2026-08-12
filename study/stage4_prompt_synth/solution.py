"""
Stage 4 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
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

    default_engine = index.as_query_engine(similarity_top_k=1)
    default_response = default_engine.query(question)
    print("=" * 20, "기본 템플릿", "=" * 20)
    print(default_response)

    custom_qa_template_str = """
너는 SEC 재무제표를 분석하는 전문 애널리스트다. 반드시 아래 문서에 나온 숫자를 그대로 인용해서 답하라.
---------------------
{context_str}
---------------------
질문: {query_str}
답변:
""".strip()
    custom_qa_prompt = QuestionAnswerPrompt(
        template=custom_qa_template_str,
        prompt_type=PromptType.QUESTION_ANSWER,
    )
    custom_synth = get_response_synthesizer(text_qa_template=custom_qa_prompt)
    custom_engine = index.as_query_engine(response_synthesizer=custom_synth, similarity_top_k=1)
    custom_response = custom_engine.query(question)

    print("\n" + "=" * 20, "커스텀 템플릿", "=" * 20)
    print(custom_response)


if __name__ == "__main__":
    main()
