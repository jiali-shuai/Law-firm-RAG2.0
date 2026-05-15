from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import create_agent

from agent.tools import search_knowledge_base, rerank_documents
from agent.prompt_loader import load_prompt

CASE_TYPE = "行政诉讼案件"
COLLECTION_NAME = "xingzheng"
LABEL = "行政诉讼律师"
PROMPT_FILE = "legal_admin_lawyer.txt"
CASE_PARAMS = {"dense_top_k": 18, "sparse_top_k": 18, "alpha": 0.40}

TOOLS = [search_knowledge_base, rerank_documents]


class AdminLawyerAgent:

    def __init__(self, chat_llm: ChatOpenAI, reasoner_llm: ChatOpenAI):
        self.chat_llm = chat_llm
        self.reasoner_llm = reasoner_llm
        self.prompt_template = load_prompt(PROMPT_FILE)

    def run(self, state: dict) -> dict:
        user_demands = state["user_demands"]
        basic_info = state["basic_info"]
        
        """设置查询参数""" 
        params = dict(CASE_PARAMS)
        overrides = state.get("_param_overrides", {})
        if CASE_TYPE in overrides:
            p = overrides[CASE_TYPE]
            if p.get("dense_top_k") is not None:
                params["dense_top_k"] = p["dense_top_k"]
            if p.get("sparse_top_k") is not None:
                params["sparse_top_k"] = p["sparse_top_k"]
            if p.get("alpha") is not None:
                params["alpha"] = p["alpha"]
        
        system_prompt = self.prompt_template.format(
            collection_name=COLLECTION_NAME,
            dense_top_k=params["dense_top_k"],
            sparse_top_k=params["sparse_top_k"],
            alpha=params["alpha"],
        )
        
        """创建智能体"""
        agent = create_agent(
            model=self.chat_llm,
            tools=TOOLS,
            system_prompt=system_prompt,
        )
        
        """执行智能体"""
        user_input = f"案件类型：{CASE_TYPE}\n用户诉求：{user_demands}\n案件基本信息：{basic_info}"

        result = agent.invoke({"messages": [HumanMessage(content=user_input)]})

        messages = result.get("messages", [])
        answer = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                answer = msg.content
                break

        return {
            "final_answer": answer,
            "messages": [AIMessage(content=f"[{LABEL}]：\n{answer}")]
        }
