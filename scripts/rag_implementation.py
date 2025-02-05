from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.prompts import ChatPromptTemplate
import json
from nemoguardrails import RailsConfig
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails

def rag_pipeline(llm, retriver=None):
    # prompt_rag = hub.pull("rlm/rag-prompt")
    # initializing the guardrails from nemo
    config = RailsConfig.from_path("config_earning_calls")
    guardrails = RunnableRails(config, input_key="query_str", output_key="answer")
    chat_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an expert Q&A system that is trusted around the world.\nAlways answer the query using the provided context information, and not prior knowledge.\nSome rules to follow:\n1. Never directly reference the given context in your answer.\n2. Avoid statements like 'Based on the context, ...' or 'The context information ...' or anything along those lines."),
            ("human", "Context information is below.\n---------------------\n{context_str}\n---------------------\nGiven the context information and not prior knowledge, answer the query.\nQuery: {query_str}\nAnswer: "),
        ]
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain_from_docs = (
        RunnablePassthrough.assign(context_str=(lambda x: format_docs(x["context_str"])))
        | chat_template
        | llm
        | StrOutputParser()
    )

    rag_chain_with_source = RunnableParallel(
        {"context_str": retriver, "query_str": RunnablePassthrough()}
    ).assign(answer=rag_chain_from_docs)

    chain_with_guardrails = guardrails | rag_chain_with_source
    
    return chain_with_guardrails, chat_template