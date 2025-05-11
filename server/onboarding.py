#!/usr/bin/env python3
# onboarding.py - Agent for answering onboarding questions from PDF documents
import asyncio
import os
import pypdf
import re
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from agents import Agent, Runner, function_tool
from azure_wrapper import init_azure_openai
try:
    from vectorizer import LocalVectorizer, embeddings_model
    VECTORIZER_AVAILABLE = True
except Exception as e:
    print(f"Vectorizer not available: {e}")
    VECTORIZER_AVAILABLE = False

# Global variables to store the onboarding documents data
ONBOARDING_DATA = {
    "first_year": {},
    "data_science": {}
}

# Paths to the PDF files
FIRST_YEAR_PDF = "Blox Connect First Year Checklist FY24.pdf"
DATA_SCIENCE_PDF = "Onboarding_dataScience.pdf"
EMBEDDINGS_FILE = "./output/embeddings.parquet"

# Flag to indicate if advanced search is available
ADVANCED_SEARCH_AVAILABLE = False

def load_pdf_content(file_path: str) -> str:
    """
    Load the content from a PDF file
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Extracted text content from the PDF
    """
    try:
        # Load the PDF
        pdf = pypdf.PdfReader(file_path)
        all_text = ""
        
        # Extract text from all pages
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"
        
        print(f"Successfully loaded content from {file_path}")
        return all_text
    except Exception as e:
        print(f"Error loading PDF data from {file_path}: {e}")
        return ""

def load_onboarding_documents():
    """
    Load and parse all onboarding documents
    """
    global ONBOARDING_DATA
    
    # Load First Year Checklist
    first_year_text = load_pdf_content(FIRST_YEAR_PDF)
    if first_year_text:
        ONBOARDING_DATA["first_year"]["full_text"] = first_year_text
        
        # Extract day-based tasks (approximation, may need refinement based on actual PDF format)
        day_patterns = {
            "day1": r"(?:Day\s*1|First\s*Day).*?(?=Day\s*[2-9]|Week|Month|\Z)",
            "week1": r"(?:Week\s*1|First\s*Week).*?(?=Week\s*[2-9]|Month|\Z)",
            "month1": r"(?:Month\s*1|First\s*Month).*?(?=Month\s*[2-9]|\Z)"
        }
        
        for key, pattern in day_patterns.items():
            match = re.search(pattern, first_year_text, re.DOTALL | re.IGNORECASE)
            if match:
                ONBOARDING_DATA["first_year"][key] = match.group(0).strip()
            else:
                ONBOARDING_DATA["first_year"][key] = ""
    
    # Load Data Science Onboarding
    ds_text = load_pdf_content(DATA_SCIENCE_PDF)
    if ds_text:
        ONBOARDING_DATA["data_science"]["full_text"] = ds_text
        
        # Extract important sections (approximation, needs refinement based on actual PDF)
        sections = {
            "tools": r"(?:Tools|Software|Applications).*?(?=\n\s*\n|\Z)",
            "teams": r"(?:Teams|Channels|Groups|Slack).*?(?=\n\s*\n|\Z)",
            "training": r"(?:Training|Learning|Courses).*?(?=\n\s*\n|\Z)"
        }
        
        for key, pattern in sections.items():
            match = re.search(pattern, ds_text, re.DOTALL | re.IGNORECASE)
            if match:
                ONBOARDING_DATA["data_science"][key] = match.group(0).strip()
            else:
                ONBOARDING_DATA["data_science"][key] = ""

def generate_embeddings():
    """
    Generate embeddings for the onboarding documents if they don't exist
    """
    global ADVANCED_SEARCH_AVAILABLE
    
    if not VECTORIZER_AVAILABLE:
        print("Vectorizer not available. Falling back to simple search.")
        ADVANCED_SEARCH_AVAILABLE = False
        return
        
    try:
        if not os.path.exists(EMBEDDINGS_FILE):
            print("Generating embeddings for onboarding documents...")
            # Create output directory if it doesn't exist
            os.makedirs("./output", exist_ok=True)
            
            vectorizer = LocalVectorizer(chunk_size=300, chunk_overlap=50)
            
            # Process both PDF files
            input_folder = os.path.dirname(os.path.abspath(__file__))
            vectorizer.run(input_folder, EMBEDDINGS_FILE)
        else:
            print(f"Using existing embeddings from {EMBEDDINGS_FILE}")
            
        # Test loading embeddings to verify they work
        test_df = load_embeddings()
        if not test_df.empty:
            ADVANCED_SEARCH_AVAILABLE = True
            print("Advanced semantic search is available.")
        else:
            ADVANCED_SEARCH_AVAILABLE = False
            print("Advanced semantic search is not available. Falling back to simple search.")
    except Exception as e:
        print(f"Error with embeddings generation: {e}")
        ADVANCED_SEARCH_AVAILABLE = False
        print("Advanced semantic search is not available. Falling back to simple search.")

def load_embeddings() -> pd.DataFrame:
    """
    Load the embeddings from the parquet file
    
    Returns:
        DataFrame containing document chunks and their embeddings
    """
    try:
        if os.path.exists(EMBEDDINGS_FILE):
            df = pd.read_parquet(EMBEDDINGS_FILE)
            print(f"Loaded {len(df)} document chunks with embeddings")
            return df
        else:
            print(f"Embeddings file not found: {EMBEDDINGS_FILE}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        return pd.DataFrame()

def search_documents(query: str, top_k: int = 5) -> List[Dict]:
    """
    Search the onboarding documents for relevant information using embeddings
    
    Args:
        query: The search query
        top_k: Number of top results to return
    
    Returns:
        List of relevant document chunks
    """
    global ADVANCED_SEARCH_AVAILABLE
    
    # If advanced search is not available, fall back to simple search
    if not ADVANCED_SEARCH_AVAILABLE:
        print("Advanced search not available. Using simple search instead.")
        return simple_search(query)
        
    try:
        # Load embeddings
        embeddings_df = load_embeddings()
        if embeddings_df.empty:
            print("Embeddings dataframe is empty. Using simple search instead.")
            return simple_search(query)
        
        # Generate embedding for the query
        query_embedding = embeddings_model.embed_query(query)
        
        # Convert embeddings to numpy arrays for faster computation
        embeddings_array = np.vstack(embeddings_df['embedding'].values)
        
        # Calculate cosine similarity
        similarities = np.dot(embeddings_array, query_embedding)
        
        # Get top_k results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "content": embeddings_df.iloc[idx]['content'],
                "score": float(similarities[idx]),
                "source": embeddings_df.iloc[idx]['title'],
            })
        
        if not results:
            print("No results from semantic search. Falling back to simple search.")
            return simple_search(query)
            
        return results
    except Exception as e:
        print(f"Error searching documents: {e}")
        print("Falling back to simple search.")
        return simple_search(query)

def simple_search(query: str) -> List[Dict]:
    """
    Simple keyword-based search as fallback if embeddings aren't available
    
    Args:
        query: The search query
    
    Returns:
        List of relevant sections
    """
    query_terms = query.lower().split()
    results = []
    
    # Search in First Year Checklist
    for key, content in ONBOARDING_DATA["first_year"].items():
        if key == "full_text":
            continue
        
        content_lower = content.lower()
        score = sum(1 for term in query_terms if term in content_lower)
        
        if score > 0:
            results.append({
                "content": content,
                "score": score,
                "source": f"First Year Checklist - {key}"
            })
    
    # Search in Data Science Onboarding
    for key, content in ONBOARDING_DATA["data_science"].items():
        if key == "full_text":
            continue
        
        content_lower = content.lower()
        score = sum(1 for term in query_terms if term in content_lower)
        
        if score > 0:
            results.append({
                "content": content,
                "score": score,
                "source": f"Data Science Onboarding - {key}"
            })
    
    # Sort by relevance score (highest first)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]  # Return top 5 results

@function_tool
async def day_one_tasks() -> str:
    """
    Get information about tasks to complete on day one
    
    Returns:
        List of tasks to complete on the first day
    """
    # Try semantic search first
    results = search_documents("what tasks should I complete on day one")
    
    if not results:
        # Fall back to extracted day 1 content
        day1_content = ONBOARDING_DATA["first_year"].get("day1", "")
        if day1_content:
            return f"Here are the tasks to complete on day one:\n\n{day1_content}"
        
        # Last resort - simple search
        simple_results = simple_search("day 1 first day tasks")
        if simple_results:
            return f"Here are the tasks to complete on day one:\n\n" + "\n\n".join([r["content"] for r in simple_results])
        
        return "I couldn't find specific information about day one tasks in the onboarding documents."
    
    # Format the semantic search results
    response = "Here are the tasks you should complete on day one:\n\n"
    for result in results:
        response += f"• {result['content']}\n\n"
    
    return response

@function_tool
async def which_teams_to_join() -> str:
    """
    Get information about which teams or channels to join
    
    Returns:
        List of teams, channels, or groups to join
    """
    # Try semantic search first
    results = search_documents("which teams or channels should I join")
    
    if not results:
        # Fall back to extracted teams content
        teams_content = ONBOARDING_DATA["data_science"].get("teams", "")
        if teams_content:
            return f"Here are the teams and channels you should join:\n\n{teams_content}"
        
        # Last resort - simple search
        simple_results = simple_search("teams channels join slack")
        if simple_results:
            return f"Here are the teams and channels you should join:\n\n" + "\n\n".join([r["content"] for r in simple_results])
        
        return "I couldn't find specific information about teams to join in the onboarding documents."
    
    # Format the semantic search results
    response = "Here are the teams and channels you should join:\n\n"
    for result in results:
        response += f"• {result['content']}\n\n"
    
    return response

@function_tool
async def first_week_tasks() -> str:
    """
    Get information about tasks to complete in the first week
    
    Returns:
        List of tasks to complete in the first week
    """
    # Try semantic search first
    results = search_documents("what tasks should I complete in the first week")
    
    if not results:
        # Fall back to extracted week 1 content
        week1_content = ONBOARDING_DATA["first_year"].get("week1", "")
        if week1_content:
            return f"Here are the tasks to complete in the first week:\n\n{week1_content}"
        
        # Last resort - simple search
        simple_results = simple_search("week 1 first week tasks")
        if simple_results:
            return f"Here are the tasks to complete in the first week:\n\n" + "\n\n".join([r["content"] for r in simple_results])
        
        return "I couldn't find specific information about first week tasks in the onboarding documents."
    
    # Format the semantic search results
    response = "Here are the tasks you should complete in the first week:\n\n"
    for result in results:
        response += f"• {result['content']}\n\n"
    
    return response

@function_tool
async def required_tools() -> str:
    """
    Get information about required tools and applications
    
    Returns:
        List of tools and applications needed for the job
    """
    # Try semantic search first
    results = search_documents("what tools and applications do I need to install")
    
    if not results:
        # Fall back to extracted tools content
        tools_content = ONBOARDING_DATA["data_science"].get("tools", "")
        if tools_content:
            return f"Here are the tools and applications you'll need:\n\n{tools_content}"
        
        # Last resort - simple search
        simple_results = simple_search("tools applications software install")
        if simple_results:
            return f"Here are the tools and applications you'll need:\n\n" + "\n\n".join([r["content"] for r in simple_results])
        
        return "I couldn't find specific information about required tools in the onboarding documents."
    
    # Format the semantic search results
    response = "Here are the tools and applications you'll need:\n\n"
    for result in results:
        response += f"• {result['content']}\n\n"
    
    return response

@function_tool
async def training_resources() -> str:
    """
    Get information about training resources and courses
    
    Returns:
        List of recommended training resources and courses
    """
    # Try semantic search first
    results = search_documents("what training resources are available")
    
    if not results:
        # Fall back to extracted training content
        training_content = ONBOARDING_DATA["data_science"].get("training", "")
        if training_content:
            return f"Here are the training resources available:\n\n{training_content}"
        
        # Last resort - simple search
        simple_results = simple_search("training courses learning resources")
        if simple_results:
            return f"Here are the training resources available:\n\n" + "\n\n".join([r["content"] for r in simple_results])
        
        return "I couldn't find specific information about training resources in the onboarding documents."
    
    # Format the semantic search results
    response = "Here are the training resources available:\n\n"
    for result in results:
        response += f"• {result['content']}\n\n"
    
    return response

@function_tool
async def search_onboarding(query: str) -> str:
    """
    Search the onboarding documents for information on a specific topic
    
    Args:
        query: The search query
    
    Returns:
        Relevant information from the onboarding documents
    """
    # Try semantic search
    results = search_documents(query)
    
    if not results:
        # Fall back to simple search
        simple_results = simple_search(query)
        if simple_results:
            response = f"Here's what I found about '{query}':\n\n"
            for result in simple_results:
                response += f"From {result['source']}:\n{result['content']}\n\n"
            return response
        
        return f"I couldn't find information about '{query}' in the onboarding documents."
    
    # Format the semantic search results
    response = f"Here's what I found about '{query}':\n\n"
    for result in results:
        response += f"From {result['source']}:\n{result['content']}\n\n"
    
    return response

async def main():
    # Load the onboarding documents
    load_onboarding_documents()
    
    # Generate embeddings if they don't exist
    generate_embeddings()
    
    # Create the agent with the onboarding tools
    try:
        client, deployment = init_azure_openai()
    except Exception as e:
        print(f"Error initializing Azure OpenAI: {e}")
        print("Using default LLM deployment.")
        client, deployment = None, None
    
    # Create the agent with the onboarding tools
    agent = Agent(
        name="Onboarding Assistant",
        model=deployment if deployment else "gpt-4o",
        instructions=(
            "You are an assistant that helps new employees with onboarding information. "
            "You can provide information about tasks to complete on the first day, first week, "
            "which teams to join, required tools, and training resources. "
            "Your knowledge comes from the 'Blox Connect First Year Checklist' and "
            "'Onboarding_dataScience' documents. "
            "Use the day_one_tasks tool when asked about what to do on the first day. "
            "Use the which_teams_to_join tool when asked about teams, channels, or groups to join. "
            "Use the first_week_tasks tool when asked about what to do in the first week. "
            "Use the required_tools tool when asked about tools or applications needed. "
            "Use the training_resources tool when asked about training or learning resources. "
            "Use the search_onboarding tool for any other specific onboarding questions. "
            "Be friendly, helpful, and concise in your responses."
        ),
        tools=[
            day_one_tasks, 
            which_teams_to_join, 
            first_week_tasks, 
            required_tools, 
            training_resources, 
            search_onboarding
        ]
    )
    
    print("Onboarding Assistant initialized. Type 'exit' or 'quit' to end the session.")
    print("=" * 60)
    print("Example queries:")
    print("- What tasks should I complete on day one?")
    print("- Which teams should I join?")
    print("- What should I do in my first week?")
    print("- What tools do I need for my job?")
    print("- What training resources are available?")
    print("- Tell me about the onboarding process")
    print("=" * 60)
    
    # Main conversation loop
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Agent: Goodbye! Good luck with your onboarding!")
            break
        
        try:
            # Process the user input and get a response using Runner
            result = await Runner.run(agent, user_input)
            
            # Display the response
            print(f"\nAgent: {result.final_output}")
        except Exception as e:
            # If there's an error with the agent, try a simple direct response
            print(f"\nError running the agent: {e}")
            
            # Simple fallback for common questions
            if "day one" in user_input.lower() or "first day" in user_input.lower():
                day1_content = ONBOARDING_DATA["first_year"].get("day1", "")
                print(f"\nAgent: Here's what I found about day one tasks:\n{day1_content}")
            elif "team" in user_input.lower() or "join" in user_input.lower():
                teams_content = ONBOARDING_DATA["data_science"].get("teams", "")
                print(f"\nAgent: Here's what I found about teams to join:\n{teams_content}")
            elif "tool" in user_input.lower() or "software" in user_input.lower():
                tools_content = ONBOARDING_DATA["data_science"].get("tools", "")
                print(f"\nAgent: Here's what I found about tools and software:\n{tools_content}")
            else:
                # Search manually for terms
                search_terms = user_input.lower().split()
                for doc_name, doc_data in ONBOARDING_DATA.items():
                    for section_name, section_content in doc_data.items():
                        if section_name == "full_text":
                            continue
                        if any(term in section_content.lower() for term in search_terms):
                            print(f"\nAgent: I found something in {doc_name} - {section_name}:\n{section_content[:300]}...")

if __name__ == "__main__":
    asyncio.run(main())