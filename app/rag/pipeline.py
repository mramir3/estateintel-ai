"""End-to-end RAG orchestrator for EstateIntel AI."""
import uuid
from typing import Dict, Any, Optional, List
from app.api.schemas import ChatRequest, ChatResponse, SourceCitation
from app.rag.retriever import retriever
from app.rag.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, COMPARISON_PROMPT_TEMPLATE
from app.services.openrouter import OpenRouterService
from app.utils.validators import sanitize_user_input, check_prompt_injection
from app.utils.logging import logger

class RAGPipeline:
    """Orchestrates query validation, hybrid context retrieval, prompt assembly, and LLM inference."""

    def __init__(self, openrouter_service: Optional[OpenRouterService] = None):
        self.openrouter = openrouter_service or OpenRouterService()
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

    def get_conversation_history(self, conv_id: str) -> List[Dict[str, str]]:
        """Retrieves active conversation history."""
        return self.conversations.get(conv_id, [])

    def add_to_history(self, conv_id: str, role: str, content: str):
        """Appends user or assistant turn to history, maintaining a sliding window of 10 messages."""
        if conv_id not in self.conversations:
            self.conversations[conv_id] = []
        self.conversations[conv_id].append({"role": role, "content": content})
        if len(self.conversations[conv_id]) > 10:
            self.conversations[conv_id] = self.conversations[conv_id][-10:]

    def format_history_text(self, conv_id: str) -> str:
        """Formats conversation history for prompt injection."""
        hist = self.get_conversation_history(conv_id)
        if not hist:
            return "No previous conversation."
        lines = []
        for turn in hist[-4:]:
            role = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{role}: {turn['content']}")
        return "\n".join(lines)

    def process_chat(self, req: ChatRequest) -> ChatResponse:
        """Processes incoming user query through complete RAG lifecycle."""
        conv_id = req.conversation_id or str(uuid.uuid4())
        raw_msg = req.message or ""

        # 1. Input Validation and Sanitization
        cleaned_msg = sanitize_user_input(raw_msg)
        if not cleaned_msg:
            return ChatResponse(
                answer="Please enter a valid real estate question or inquiry.",
                conversation_id=conv_id,
                model=self.openrouter.primary_model,
                status="error",
                error="Empty input query"
            )

        # 2. Prompt Injection Defense
        if check_prompt_injection(cleaned_msg):
            logger.warning(f"Prompt injection pattern detected in query: {cleaned_msg[:100]}")
            return ChatResponse(
                answer=(
                    "I am EstateIntel AI, dedicated to providing grounded intelligence on DarGlobal developments "
                    "and Wasalt property listings. I cannot fulfill requests that attempt to alter system directives "
                    "or access restricted system operations. How can I assist you with real estate exploration today?"
                ),
                conversation_id=conv_id,
                model=self.openrouter.primary_model,
                status="rejected",
                error="Security policy triggered"
            )

        # 3. Hybrid Context Retrieval
        properties, citations, context_text = retriever.retrieve(
            query=cleaned_msg,
            explicit_filters=req.filters
        )

        # Check for insufficient context / out-of-scope query
        # If no properties returned or relevance is virtually 0
        if not properties:
            unverified_ans = "I couldn't verify that information from the available DarGlobal or Wasalt sources."
            self.add_to_history(conv_id, "user", cleaned_msg)
            self.add_to_history(conv_id, "assistant", unverified_ans)
            return ChatResponse(
                answer=unverified_ans,
                conversation_id=conv_id,
                model=self.openrouter.primary_model,
                sources=[],
                retrieved_count=0,
                status="insufficient_context"
            )

        # 4. Prompt Construction
        history_text = self.format_history_text(conv_id)
        is_comparison = any(w in cleaned_msg.lower() for w in ["compare", "comparison", "difference between", "versus", "vs"])
        template = COMPARISON_PROMPT_TEMPLATE if is_comparison else USER_PROMPT_TEMPLATE

        user_prompt = template.format(
            context=context_text,
            history=history_text,
            question=cleaned_msg
        )

        # 5. LLM Inference via OpenRouter Free Model
        answer_text, model_used, error = self.openrouter.generate_response(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            history=self.get_conversation_history(conv_id)
        )

        # 6. Update Conversation History
        self.add_to_history(conv_id, "user", cleaned_msg)
        self.add_to_history(conv_id, "assistant", answer_text)

        return ChatResponse(
            answer=answer_text,
            conversation_id=conv_id,
            model=model_used,
            sources=citations,
            retrieved_count=len(properties),
            status="success" if not error else "partial_error",
            error=error
        )

rag_pipeline = RAGPipeline()
