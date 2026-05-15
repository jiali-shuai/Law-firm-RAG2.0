import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage

from agent.prompt_loader import load_prompt

COLLECTION_MAP = {
    "民商事诉讼案件": "minshi",
    "刑事辩护案件": "xingshi",
    "行政诉讼案件": "xingzheng",
}

"""兜底json解析:健壮化补丁"""
def _parse_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    if not text:
        raise ValueError("LLM 返回空内容")
    return json.loads(text)

"""接待员智能体"""
class ReceptionAgent:

    def __init__(self, chat_llm: ChatOpenAI):
        self.chat_llm = chat_llm
        self.prompt = load_prompt("legal_reception.txt")

    """接待员智能体运行"""
    def run(self, state: dict) -> dict:
        question = state["question"]
        conversation_context = state.get("_conversation_context", "")

        user_input = f"【对话历史】\n{conversation_context}\n\n【用户最新消息】\n{question}" if conversation_context else question

        response = self.chat_llm.invoke([
            ("system", self.prompt),
            ("user", user_input)
        ])
        result = _parse_json(response.content)

        """判断三要素是否完成"""
        complete = result.get("complete", False)

        if not complete:
            follow_up = result.get("follow_up", "请详细描述您的案件情况。")
            return {
                "_needs_followup": True,
                "_followup_question": follow_up,
                "messages": [AIMessage(content=follow_up)],
            }
        """提取三要素并决定collection"""
        case_type = result.get("案件类型", "其他")
        user_demands = result.get("用户诉求", "")
        basic_info = result.get("案件基本信息", "")
        collection_name = COLLECTION_MAP.get(case_type, "")

        return {
            "_needs_followup": False,
            "case_type": case_type,
            "user_demands": user_demands,
            "basic_info": basic_info,
            "retrieval_collection": collection_name,
            "messages": [AIMessage(content=f"案件类型：{case_type}\n诉求：{user_demands}\n基本信息：{basic_info}")],
        }
