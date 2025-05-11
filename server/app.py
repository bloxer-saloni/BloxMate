#!/usr/bin/env python3
# app.py - Streamlit UI for the supervisor agent chatbot
import streamlit as st
import asyncio
import nest_asyncio
import re
from supervisor import SupervisorAgent

# Apply nest_asyncio to allow asyncio to work in Streamlit
nest_asyncio.apply()

# Page configuration
st.set_page_config(
    page_title="BloxMate",
    page_icon="🤖",
    layout="wide"
)

# CSS for better UI with highlighted main answer
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .user-message {
        background-color: #e6f7ff;
        border-left: 5px solid #1890ff;
    }
    .assistant-message {
        background-color: #f6ffed;
        border-left: 5px solid #52c41a;
    }
    .css-18e3th9 {
        padding-top: 0;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    .stMarkdown p {
        margin-bottom: 0;
    }
    
    /* Styling for the main answer box */
    .main-answer {
        background-color: #f8f9fa;
        border-left: 5px solid #4CAF50;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Styling for metadata (analysis, routing) */
    .metadata {
        font-size: 0.8em;
        color: #6c757d;
        padding: 5px 0;
        margin-bottom: 10px;
        border-bottom: 1px solid #e9ecef;
    }
    
    /* Answer styling */
    .answer-header {
        font-weight: bold;
        color: #2C3E50;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'agent' not in st.session_state:
        st.session_state.agent = SupervisorAgent()

def format_response(response):
    """Format the response to highlight the main answer and reduce prominence of metadata"""
    if not response:
        return "No response generated."

    # Extract the metadata (analyzing, routing parts)
    metadata_parts = []
    
    # Look for analyzing message
    analyzing_match = re.search(r"🤔\s+Analyzing\s+your\s+question.*?(?=\n\n|\n[📚🎓👥🤝])", response, re.DOTALL)
    if analyzing_match:
        metadata_parts.append(analyzing_match.group(0).strip())
    
    # Look for routing message
    routing_patterns = [
        r"(📚\s+Routing\s+to\s+Knowledge\s+Base\s+Agent.*?)(?=\n\n|💬)",
        r"(🎓\s+Routing\s+to\s+Learning\s+Assistant.*?)(?=\n\n)",
        r"(👥\s+Routing\s+to\s+Org\s+Chart\s+Assistant.*?)(?=\n\n)",
        r"(🤝\s+Routing\s+to\s+Workplace\s+Communication\s+Assistant.*?)(?=\n\n)"
    ]
    
    for pattern in routing_patterns:
        route_match = re.search(pattern, response, re.DOTALL)
        if route_match:
            metadata_parts.append(route_match.group(1).strip())
            break
    
    # Extract the main answer based on agent type
    main_answer = ""
    answer_title = "Response"
    
    # For Knowledge Base Agent (RAG or GPT-4o answers)
    rag_match = re.search(r"💬\s+RAG\s+Answer:(.*?)(?=⚠️|\n\n\n|$)", response, re.DOTALL | re.IGNORECASE)
    gpt_match = re.search(r"💬\s+GPT-4o\s+Answer:(.*?)(?=⚠️|\n\n\n|$)", response, re.DOTALL | re.IGNORECASE)
    enhanced_match = re.search(r"💬\s+Enhanced\s+Answer\s+from\s+Online\s+Sources:(.*?)$", response, re.DOTALL | re.IGNORECASE)
    
    # For Org Chart Assistant
    org_chart_match = re.search(r"Org\s+Chart\s+Assistant:\s+(.*?)$", response, re.DOTALL)
    
    # For Workplace Communication Assistant
    workplace_match = re.search(r"🤝\s+Routing\s+to\s+Workplace.*?\n\n(.*?)$", response, re.DOTALL)
    
    # For Learning Assistant
    learning_match = re.search(r"🎓\s+Routing\s+to\s+Learning\s+Assistant.*?\n\n(.*?)$", response, re.DOTALL)
    
    # Determine which match to use for the main answer
    if enhanced_match:
        answer_title = "Enhanced Answer from Online Sources"
        main_answer = enhanced_match.group(1).strip()
    elif rag_match:
        answer_title = "Knowledge Base Answer"
        main_answer = rag_match.group(1).strip()
    elif gpt_match:
        answer_title = "Knowledge Base Answer"
        main_answer = gpt_match.group(1).strip()
    elif org_chart_match:
        answer_title = "Organization Information"
        main_answer = org_chart_match.group(1).strip()
    elif workplace_match:
        answer_title = "Workplace Communication"
        main_answer = workplace_match.group(1).strip()
    elif learning_match:
        answer_title = "Learning Resources"
        main_answer = learning_match.group(1).strip()
    else:
        # If no specific pattern matched, use everything after routing as the main answer
        for part in metadata_parts:
            response = response.replace(part, "")
        main_answer = response.strip()
    
    # Format the response with HTML
    formatted_html = ""
    
    # Add metadata with smaller font
    if metadata_parts:
        formatted_html += f'<div class="metadata">{" ".join(metadata_parts)}</div>'
    
    # Add the main answer with highlighted styling
    formatted_html += f'<div class="main-answer"><p class="answer-header">{answer_title}</p>{main_answer}</div>'
    
    return formatted_html

async def process_query(query):
    """Process user query and return the response"""
    try:
        # Direct call to the route_query method of the supervisor agent
        response = await st.session_state.agent.route_query(query)
        return response
    except Exception as e:
        import traceback
        return f"Error processing query: {str(e)}\n\n{traceback.format_exc()}"

def main():
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("🤖 BloxMate Assistant")
    
    # Sidebar with capabilities info
    with st.sidebar:
        st.header("Capabilities")
        st.markdown("""
        I can answer questions about:
        - 📚 Products, resources, and documentation
        - 🎓 Learning recommendations from LinkedIn Learning
        - 👥 Organization structure, employees, and managers
        - 🔍 Finding people working on specific topics or projects
        - 🤝 Workplace communication and the "no jerks" policy
        """)
        
        # Optional: Add reset button
        if st.button("Reset Conversation"):
            st.session_state.messages = []
            st.rerun()
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                if message.get("formatted", False):
                    st.markdown(message["content"], unsafe_allow_html=True)
                else:
                    st.markdown(message["content"])
    
    # Chat input
    query = st.chat_input("How can I help you today?")
    
    # Process the query when submitted
    if query:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Display user message
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(query)
        
        # Display assistant response
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤔 Thinking...")
            
            try:
                # Create a new asyncio event loop for this execution
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Process the query and get response using the loop
                response = loop.run_until_complete(process_query(query))
                loop.close()
                
                # Update the placeholder with the formatted response
                if response:
                    formatted_response = format_response(response)
                    message_placeholder.markdown(formatted_response, unsafe_allow_html=True)
                    
                    # Add formatted response to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": formatted_response,
                        "formatted": True
                    })
                else:
                    message_placeholder.markdown("I'm sorry, I couldn't generate a response. Please try again.")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "I'm sorry, I couldn't generate a response. Please try again."
                    })
            except Exception as e:
                import traceback
                error_message = f"Error processing your request: {str(e)}\n\n```\n{traceback.format_exc()}\n```"
                message_placeholder.markdown(error_message)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_message
                })

if __name__ == "__main__":
    main()