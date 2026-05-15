from fastapi import APIRouter
from pydantic import BaseModel

from llmodel.llm import CHAT_LLM, REASONER_LLM
from agent.legal_graph import LegalGraph

router = APIRouter()

class ParamOverride(BaseModel):
    dense_top_k: int   # 密集召回的前k个结果数量
    sparse_top_k: int   # 稀疏召回的前k个结果数量
    alpha: float   # 混合召回的权重参数，用于平衡密集召回和稀疏召回的结果

class LegalChatRequest(BaseModel):
    question: str
    session_id: str
    param_overrides: dict[str, ParamOverride] = {}


class LegalChatResponse(BaseModel):
    answer: str
    case_type: str
    session_id: str
    needs_followup: bool = False


_legal_sessions = {}

"""法律咨询接口"""
@router.post("/api/legal/chat", response_model=LegalChatResponse)
def legal_chat(req: LegalChatRequest):
    
    session = _legal_sessions.get(req.session_id)

    if session and session.get("completed"):
        return LegalChatResponse(
            answer="本次咨询已结束，请刷新页面开始新的会话。",
            case_type=session.get("case_type", ""),
            session_id=req.session_id,
            needs_followup=False,
        )

    chat_llm = CHAT_LLM
    reasoner_llm = REASONER_LLM
    legal_graph = LegalGraph(chat_llm, reasoner_llm)
    """构建对话上下文"""
    history_parts = []
    if session:
        for turn in session.get("history", []):
            history_parts.append(f"用户：{turn['user']}")
            history_parts.append(f"接待员：{turn['assistant']}")
    conversation_context = "\n".join(history_parts)
    """构建参数覆盖"""
    overrides = {}
    for case_type, p in req.param_overrides.items():
        overrides[case_type] = {
            "dense_top_k": p.dense_top_k,
            "sparse_top_k": p.sparse_top_k,
            "alpha": p.alpha,
        }
    """调用法律咨询模型"""
    result = legal_graph.invoke(
        req.question,
        conversation_context=conversation_context,
        param_overrides=overrides,
    )
    """需要继续咨询"""
    if result["needs_followup"]:
        if not session:
            session = {"history": [], "completed": False, "case_type": ""}
        session["history"].append({
            "user": req.question,
            "assistant": result["followup_question"],
        })
        _legal_sessions[req.session_id] = session
        return LegalChatResponse(
            answer=result["followup_question"],
            case_type="",
            session_id=req.session_id,
            needs_followup=True,
        )
    """咨询结束"""
    if not session:
        session = {"history": [], "completed": False, "case_type": ""}
    session["completed"] = True
    session["case_type"] = result["case_type"]
    _legal_sessions[req.session_id] = session
    return LegalChatResponse(
        answer=result["answer"],
        case_type=result["case_type"],
        session_id=req.session_id,
        needs_followup=False,
    )
