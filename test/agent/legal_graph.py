from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages


from agent.reception_agent import ReceptionAgent
from agent.civil_lawyer_agent import CivilLawyerAgent
from agent.criminal_lawyer_agent import CriminalLawyerAgent
from agent.admin_lawyer_agent import AdminLawyerAgent


NOT_ACCEPTED = "本律所暂时无法受理"


class LegalState(TypedDict):
    messages: Annotated[list, add_messages]  # LangGraph 标准消息列表，用于保存图内交互历史
    question: str  # 用户当前提问内容
    case_type: str  # 案件类型：民商事诉讼案件 | 刑事辩护案件 | 行政诉讼案件 | 其他
    user_demands: str  # 用户诉求摘要
    basic_info: str  # 案件基本信息
    retrieval_collection: str  # 对应的 Milvus 向量集合名：minshi | xingshi | xingzheng
    final_answer: str  # 最终法律分析意见
    _param_overrides: dict  # 前端传入的参数覆盖：{案件类型: {dense_top_k, sparse_top_k, alpha}}
    _needs_followup: bool  # 是否需要继续追问用户（仅在 reception 阶段使用）
    _followup_question: str  # 追问用户的具体问题
    _conversation_context: str  # 来自 API 的完整多轮对话历史，供 reception 使用


def _route_after_reception(state: LegalState) -> str:
    if state.get("_needs_followup"):
        return "followup_end"
    case_type = state.get("case_type", "其他")
    if case_type in ("民商事诉讼案件", "刑事辩护案件", "行政诉讼案件"):
        return case_type
    return "reject"

"""拒绝回答无关案件类型"""
def _reject_agent(state: LegalState) -> dict:
    return {
        "final_answer": NOT_ACCEPTED,
        "messages": [AIMessage(content=NOT_ACCEPTED)]
    }


class LegalGraph:

    def __init__(self, chat_llm: ChatOpenAI, reasoner_llm: ChatOpenAI):
        self.reception = ReceptionAgent(chat_llm)
        self.civil_lawyer = CivilLawyerAgent(chat_llm, reasoner_llm)
        self.criminal_lawyer = CriminalLawyerAgent(chat_llm, reasoner_llm)
        self.admin_lawyer = AdminLawyerAgent(chat_llm, reasoner_llm)
        self.graph = self._build_graph()

    """构建agent图"""
    def _build_graph(self) -> StateGraph:
        graph = StateGraph(LegalState)
        """构建agent节点"""
        graph.add_node("reception", self.reception.run)
        graph.add_node("civil_lawyer", self.civil_lawyer.run)
        graph.add_node("criminal_lawyer", self.criminal_lawyer.run)
        graph.add_node("admin_lawyer", self.admin_lawyer.run)
        graph.add_node("reject", _reject_agent)
        """构建agent条件边"""
        graph.set_entry_point("reception")

        graph.add_conditional_edges(
            "reception",
            _route_after_reception,
            {
                "民商事诉讼案件": "civil_lawyer",
                "刑事辩护案件": "criminal_lawyer",
                "行政诉讼案件": "admin_lawyer",
                "reject": "reject",
                "followup_end": END,
            }
        )

        graph.add_edge("civil_lawyer", END)
        graph.add_edge("criminal_lawyer", END)
        graph.add_edge("admin_lawyer", END)
        graph.add_edge("reject", END)

        return graph.compile()
    
    """封装agent图运行"""
    def invoke(self, question: str, messages: list = None,
               conversation_context: str = "", param_overrides: dict = None) -> dict:
        initial_state: LegalState = {
            "messages": messages or [],
            "question": question,
            "case_type": "",
            "user_demands": "",
            "basic_info": "",
            "retrieval_collection": "",
            "final_answer": "",
            "_param_overrides": param_overrides or {},
            "_needs_followup": False,
            "_followup_question": "",
            "_conversation_context": conversation_context,
        }
        result = self.graph.invoke(initial_state)
        return {
            "answer": result.get("final_answer", ""),
            "case_type": result.get("case_type", "其他"),
            "messages": result.get("messages", []),
            "needs_followup": result.get("_needs_followup", False),
            "followup_question": result.get("_followup_question", ""),
        }
