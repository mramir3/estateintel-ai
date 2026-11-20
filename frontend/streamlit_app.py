"""EstateIntel AI - Streamlit Web Interface."""
import sys
import uuid
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.rag.pipeline import rag_pipeline
from app.api.schemas import ChatRequest
from app.services.property_service import property_service
from app.config import settings

# Page setup
st.set_page_config(
    page_title="EstateIntel AI — DarGlobal × Wasalt Assistant",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
css_path = ROOT_DIR / "frontend" / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Session state initialization
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "preset_prompt" not in st.session_state:
    st.session_state.preset_prompt = None

# Sidebar
with st.sidebar:
    st.markdown("### 🏢 EstateIntel AI")
    st.markdown("**DarGlobal & Wasalt Intelligence Assistant**")
    st.markdown("---")
    
    # Live stats
    sources_data = property_service.get_sources_overview()
    total_props = sources_data.get("total_properties", 0)
    dg_props = sources_data.get("sources", {}).get("DarGlobal", {}).get("count", 0)
    wasalt_props = sources_data.get("sources", {}).get("Wasalt", {}).get("count", 0)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Indexed", total_props)
    with col2:
        st.metric("DarGlobal", dg_props)
    st.metric("Wasalt Verified", wasalt_props)

    st.markdown("---")
    st.markdown("#### 🤖 Model Configuration")
    st.markdown(f"**Engine:** `OpenRouter API`")
    st.markdown(f"**Model:** `{settings.OPENROUTER_MODEL}`")
    st.markdown(f"**Embeddings:** `{settings.EMBEDDING_MODEL_NAME}`")
    
    st.markdown("---")
    st.markdown("#### 💡 Example Questions")
    
    sample_questions = [
        "Tell me about DarGlobal.",
        "What developments are included in the database?",
        "Compare DarGlobal luxury towers in Dubai.",
        "Find Wasalt listings in Riyadh under SAR 2,000,000.",
        "What amenities are available at Tierra Viva by Lamborghini?",
        "Which developments are located in Saudi Arabia?",
        "Show me golf community developments.",
        "ما هي الفلل المتاحة في الرياض؟"
    ]

    for q in sample_questions:
        if st.button(q, key=f"btn_{q}"):
            st.session_state.preset_prompt = q

    st.markdown("---")
    col_clear, col_export = st.columns(2)
    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_id = str(uuid.uuid4())
            st.rerun()
    with col_export:
        if st.session_state.messages:
            chat_export = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            st.download_button(
                "📥 Export",
                data=chat_export,
                file_name="estateintel_conversation.txt",
                mime="text/plain",
                use_container_width=True
            )

# Main Header
st.markdown("""
<div class="main-header">
    <span class="badge-gold">Verified Enterprise Intelligence</span>
    <h1>EstateIntel AI</h1>
    <p>Explore DarGlobal developments and Wasalt property information with AI.</p>
</div>
""", unsafe_allow_html=True)

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"📚 Verified Sources & References ({len(msg['sources'])})", expanded=False):
                for s in msg["sources"]:
                    src_class = "badge-source-dg" if s["source"] == "DarGlobal" else "badge-source-wasalt"
                    price_str = f"• {s['price']:,.0f} {s['currency']}" if s.get("price") else ""
                    loc_str = f"• {s['location']}" if s.get("location") else ""
                    score_str = f"• Relevance: {int(s['relevance_score']*100)}%" if s.get("relevance_score") else ""
                    
                    st.markdown(f"""
                    <div class="citation-container">
                        <div class="citation-title">
                            <span class="{src_class}">{s['source']}</span> 
                            <a href="{s['source_url']}" target="_blank" style="text-decoration: none; font-weight: 600; color: #0284c7;">
                                {s['title']} ↗
                            </a>
                        </div>
                        <div class="citation-meta">
                            {loc_str} {price_str} {score_str}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# Handle user input (from chat_input or preset button)
prompt_input = st.chat_input("Ask about DarGlobal developments, Wasalt listings, prices, or locations...")
user_query = st.session_state.preset_prompt or prompt_input

if user_query:
    st.session_state.preset_prompt = None
    
    # Display user turn
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Process Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Searching verified real estate records and generating grounded response..."):
            req = ChatRequest(
                message=user_query,
                conversation_id=st.session_state.conversation_id
            )
            response = rag_pipeline.process_chat(req)
            
            st.markdown(response.answer)
            
            # Display citations
            sources_dict = [s.model_dump() for s in response.sources]
            if sources_dict:
                with st.expander(f"📚 Verified Sources & References ({len(sources_dict)})", expanded=True):
                    for s in sources_dict:
                        src_class = "badge-source-dg" if s["source"] == "DarGlobal" else "badge-source-wasalt"
                        price_str = f"• {s['price']:,.0f} {s['currency']}" if s.get("price") else ""
                        loc_str = f"• {s['location']}" if s.get("location") else ""
                        score_str = f"• Relevance: {int(s['relevance_score']*100)}%" if s.get("relevance_score") else ""
                        
                        st.markdown(f"""
                        <div class="citation-container">
                            <div class="citation-title">
                                <span class="{src_class}">{s['source']}</span> 
                                <a href="{s['source_url']}" target="_blank" style="text-decoration: none; font-weight: 600; color: #0284c7;">
                                    {s['title']} ↗
                                </a>
                            </div>
                            <div class="citation-meta">
                                {loc_str} {price_str} {score_str}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.answer,
                "sources": sources_dict
            })
