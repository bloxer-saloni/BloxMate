#!/usr/bin/env python3
# supervisor.py - Agent that routes user queries to specialized agents
import asyncio
import re
import requests
import sys
import io
from typing import Tuple, List, Dict, Any
from bs4 import BeautifulSoup

# Import specialized agents
from azure_wrapper import init_azure_openai
import response as kb_response # For product/documentation related queries
import linkedin # For learning related queries
import org_chart_bot # For organization chart related queries
import workplace_comms # For workplace communication and "no jerks" policy
import onboarding # For employee onboarding information

# Initialize Azure OpenAI client
azure_client, deployment = init_azure_openai()

# Regular expressions to detect insufficient answers
INSUFFICIENT_ANSWER_PATTERNS = [
    r"does not contain .* information",
    r"may need to refer to additional resources",
    r"no(t| detailed| specific) information .* (available|found|provided)",
    r"cannot provide .* (details|information)",
    r"I don't have .* specific information",
    r"The context .* doesn't mention",
    r"not mentioned in the context",
    r"no mention of .* in the provided context",
]

class SupervisorAgent:
    def __init__(self):
        # Initialize the specialized agents' data
        # Load org chart data for the org_chart_bot
        org_chart_bot.ORG_CHART_DATA = org_chart_bot.load_org_chart()
        # Load weekly update data for the org_chart_bot
        org_chart_bot.WEEKLY_UPDATE_DATA = org_chart_bot.load_weekly_updates()
        # Initialize workplace_comms with Azure client info
        workplace_comms.azure_client = azure_client
        workplace_comms.deployment = deployment
    
    async def classify_query(self, query: str) -> Tuple[str, float]:
        """
        Classify the user query to determine which specialized agent should handle it.
        
        Args:
            query: The user's question or request
            
        Returns:
            Tuple containing (agent_type, confidence_score)
        """
        prompt = f"""
        Analyze the following user query and determine which specialized agent should handle it:
        
        User query: "{query}"
        
        Options:
        1. "product" - For questions about products, resources, documentation, benfits, policies or Infoblox
        2. "learning" - For queries about learning new skills or looking for LinkedIn Learning courses
        3. "org_chart" - For questions about employees, managers, or organizational structure
        4. "workplace_comms" - For questions about workplace communication, handling difficult conversations, or applying the "no jerks" policy
        5. "onboarding" - For questions about employee onboarding, first day tasks, required tools, teams to join, or training resources
        
        Return one of the options and a confidence score (0-1) in this exact format:
        AGENT:option_name|CONFIDENCE:score
        """
        
        response = await azure_client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a helpful AI that classifies user queries for appropriate routing to specialized agents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip()
        
        # Extract the agent type and confidence using regex
        agent_match = re.search(r"AGENT:(product|learning|org_chart|workplace_comms|onboarding)", result)
        confidence_match = re.search(r"CONFIDENCE:([0-9]\.[0-9]+)", result)
        
        if agent_match and confidence_match:
            agent_type = agent_match.group(1)
            confidence = float(confidence_match.group(1))
            return (agent_type, confidence)
        else:
            # Default to product agent with low confidence if parsing fails
            return ("product", 0.5)
    
    async def route_query(self, query: str):
        """
        Route the user query to the appropriate specialized agent and return the response.
        
        Args:
            query: The user's question or request
            
        Returns:
            Response from the specialized agent
        """
        # Classify the query
        agent_type, confidence = await self.classify_query(query)

        # Route to the appropriate agent and suppress unnecessary output
        if (agent_type == "product" and confidence >= 0.6):
            # Display which agent is responding
            print(f"\n🔍 BloxMate Knowledge Base Agent:\n")
            
            # Capture the output instead of printing directly
            old_stdout = sys.stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            try:
                if kb_response.is_infoblox_query(query):
                    # For Infoblox queries, use direct GPT-4o
                    kb_response.answer_direct_gpt(query)
                else:
                    # Use RAG for other product/doc queries
                    vectorstore = kb_response.load_cached_vectorstore(
                        "./output/embeddings.parquet", 
                        "./output/faiss_index"
                    )
                    kb_response.run_rag_query(query, vectorstore)
                
                # Get the captured output
                sys.stdout = old_stdout
                output = captured_output.getvalue()
                
                # Extract only the answer part
                answer_lines = output.split('\n')
                rag_answer = ""
                capture_answer = False
                
                for line in answer_lines:
                    if "💬 RAG Answer:" in line or "💬 GPT-4o Answer:" in line:
                        capture_answer = True
                        continue
                    if capture_answer:
                        rag_answer += line + "\n"
                
                # Print only the clean answer
                if rag_answer.strip():
                    print(rag_answer.strip())
                else:
                    print("I don't have enough information to answer that question based on my knowledge.")
                
                # Check if the answer is insufficient
                if rag_answer and await self.is_insufficient_answer(rag_answer):
                    # Reset stdout capturing for online search
                    captured_output = io.StringIO()
                    sys.stdout = captured_output
                    
                    # Get a more comprehensive answer from online sources
                    online_answer = await self.search_online_and_respond(query, rag_answer)
                    
                    # Restore stdout and get captured output
                    sys.stdout = old_stdout
                    online_captured = captured_output.getvalue()
                    
                    # Print only the enhanced answer
                    print(online_answer)
                
            except Exception as e:
                sys.stdout = old_stdout
                print("I'm sorry, I couldn't retrieve that information at the moment. Please try again or ask something else.")
                
        elif agent_type == "learning" and confidence >= 0.6:
            # Display which agent is responding
            print(f"\n🎓 BloxMate LinkedIn Learning Assistant:\n")
            
            try:
                # For learning queries, use the LinkedIn learning agent
                courses = linkedin.search_linkedin_courses(query)
                
                if any("error" in course for course in courses):
                    print("I couldn't find any relevant LinkedIn Learning courses for your query. Please try a different search term.")
                else:
                    enhanced_courses = await linkedin.process_courses(courses)
                    for course in enhanced_courses:
                        # Print the course information with proper formatting
                        print(course)
                        print("-" * 40)
            except Exception as e:
                print("I'm sorry, I couldn't retrieve LinkedIn Learning courses at the moment. Please try again later.")
                
        elif agent_type == "org_chart" and confidence >= 0.6:
            # Display which agent is responding
            print(f"\n👥 BloxMate Organization Assistant:\n")
            
            # Capture the output
            old_stdout = sys.stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            try:
                # For org chart queries, use the org chart bot
                agent = org_chart_bot.Agent(
                    name="OrgChart and Project Assistant",
                    model=deployment,
                    instructions=(
                        "You are an assistant that helps with organization and project information. "
                        "You can provide information about employees, their roles, and their current projects. "
                        "Users can ask about an employee's job title and manager, or who reports to a specific manager. "
                        "They can also ask about who is working on specific topics or projects based on the weekly status updates, "
                        "or who to contact for information on specific topics like certifications or security logs. "
                        "Use the lookup_employee tool when asked about a specific person's role or manager. "
                        "Use the list_employees_under_manager tool when asked who reports to someone. "
                        "Use the find_people_working_on tool when asked about who's working on a specific project or topic. "
                        "Use the who_to_contact_for tool when asked who they should talk to about a specific topic. "
                        "Be friendly and concise in your responses."
                    ),
                    tools=[
                        org_chart_bot.lookup_employee,
                        org_chart_bot.list_employees_under_manager,
                        org_chart_bot.find_people_working_on,
                        org_chart_bot.who_to_contact_for
                    ]
                )
                
                result = await org_chart_bot.Runner.run(agent, query)
                
                # Restore stdout
                sys.stdout = old_stdout
                
                # Print only the clean answer
                print(result.final_output)
                
            except Exception as e:
                sys.stdout = old_stdout
                print("I'm sorry, I couldn't retrieve organization information at the moment. Please try again later.")
            
        elif agent_type == "workplace_comms" and confidence >= 0.6:
            # Display which agent is responding
            print(f"\n🤝 BloxMate Workplace Communication Assistant:\n")
            
            # Capture the output
            old_stdout = sys.stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            try:
                # For workplace communication queries, use the workplace communication agent
                comms_response = await workplace_comms.handle_workplace_query(query)
                
                # Restore stdout
                sys.stdout = old_stdout
                
                # Print the clean response
                print(comms_response)
                
            except Exception as e:
                sys.stdout = old_stdout
                print("I'm sorry, I couldn't process your workplace communication query at the moment. Please try again later.")
            
        elif agent_type == "onboarding" and confidence >= 0.6:
            # Display which agent is responding
            print(f"\n🚀 BloxMate Onboarding Assistant:\n")
            
            # Capture the output
            old_stdout = sys.stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            try:
                # First ensure the onboarding documents are loaded
                onboarding.load_onboarding_documents()
                
                # Make sure embeddings are ready for advanced search
                onboarding.generate_embeddings()
                
                # Create the onboarding agent with the appropriate tools
                agent = onboarding.Agent(
                    name="Onboarding Assistant",
                    model=deployment,
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
                        onboarding.day_one_tasks, 
                        onboarding.which_teams_to_join, 
                        onboarding.first_week_tasks, 
                        onboarding.required_tools, 
                        onboarding.training_resources, 
                        onboarding.search_onboarding
                    ]
                )
                
                # Run the onboarding agent with the user's query
                result = await onboarding.Runner.run(agent, query)
                
                # Restore stdout
                sys.stdout = old_stdout
                
                # Print only the clean answer
                print(result.final_output)
                
            except Exception as e:
                sys.stdout = old_stdout
                print("I'm sorry, I couldn't retrieve onboarding information at the moment. Please try again later.")
                
                # Simple fallback in case of agent error - but without showing errors
                try:
                    # Try to use a simple direct search if the agent fails
                    results = onboarding.simple_search(query)
                    if results:
                        print("Here's some onboarding information that might help:")
                        for result in results:
                            print(f"\n- From {result['source']}:")
                            print(result['content'][:300] + "..." if len(result['content']) > 300 else result['content'])
                    else:
                        print("I couldn't find specific onboarding information for your query.")
                except Exception:
                    pass
            
        else:
            # Display default message for unrecognized queries
            print("\n❓ BloxMate Assistant:\n")
            print("I'm not sure I understand your request. I can help with:")
            print("- Information about Infoblox products and documentation")
            print("- LinkedIn Learning course recommendations")
            print("- Organization structure and employee information")
            print("- Workplace communication guidance")
            print("- Employee onboarding resources")
            print("\nPlease try asking about one of these topics.")

    async def search_web(self, query: str, num_results: int = 3) -> List[Dict[str, str]]:
        """
        Search the web for information about a query.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of dictionaries containing title, url, and snippet for each result
        """
        print(f"\n🔎 Searching the web for more information about: {query}")
        
        # Format the query for search
        search_query = f"infoblox {query}"
        
        try:
            # Use a search API or directly scrape search results
            # This is a simplified implementation using direct requests
            # In production, you would use a proper search API
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            response = requests.get(search_url, headers=headers)
            
            if response.status_code != 200:
                return [{"title": "Error", "url": "", "snippet": f"Failed to search. Status code: {response.status_code}"}]
            
            # Parse search results
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = []
            
            # Extract search results (simplified, would need to be adapted to actual HTML structure)
            result_divs = soup.find_all('div', class_='g')
            for div in result_divs[:num_results]:
                try:
                    title_elem = div.find('h3')
                    link_elem = div.find('a')
                    snippet_elem = div.find('div', class_='VwiC3b')
                    
                    title = title_elem.text if title_elem else "No title"
                    url = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                    snippet = snippet_elem.text if snippet_elem else "No description"
                    
                    if url.startswith('/url?'):
                        url = url.split('q=')[1].split('&')[0]
                    
                    search_results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
                except Exception as e:
                    continue
                
                if len(search_results) >= num_results:
                    break
            
            return search_results
        except Exception as e:
            return [{"title": "Error", "url": "", "snippet": f"Failed to search: {str(e)}"}]

    async def fetch_webpage_content(self, url: str) -> str:
        """
        Fetch and extract the main content from a webpage.
        
        Args:
            url: URL of the webpage to fetch
            
        Returns:
            Extracted main content from the webpage
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return f"Failed to fetch the webpage. Status code: {response.status_code}"
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text and clean it
            text = soup.get_text(separator='\n')
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit the text length to avoid token limits
            if len(text) > 10000:
                text = text[:10000] + "... [text truncated]"
                
            return text
        except Exception as e:
            return f"Error fetching webpage: {str(e)}"

    async def is_insufficient_answer(self, answer: str) -> bool:
        """
        Check if the answer indicates insufficient information.
        
        Args:
            answer: The answer to check
            
        Returns:
            True if the answer indicates insufficient information, False otherwise
        """
        # Check if the answer matches any of the insufficient answer patterns
        for pattern in INSUFFICIENT_ANSWER_PATTERNS:
            if re.search(pattern, answer, re.IGNORECASE):
                return True
        
        return False

    async def search_online_and_respond(self, query: str, initial_answer: str = None) -> str:
        """
        Search online for information and generate a comprehensive response.
        
        Args:
            query: The user's query
            initial_answer: The initial answer from the local system (if any)
            
        Returns:
            A comprehensive response based on online information
        """
        print("\n🌐 Searching online for more comprehensive information...")
        
        # Search web for relevant pages
        search_results = await self.search_web(query)
        
        if not search_results or "Error" in search_results[0]["title"]:
            return "I couldn't find additional information online. Please try a more specific query or check official Infoblox documentation."
        
        # Fetch and extract content from the top results
        content_pieces = []
        for i, result in enumerate(search_results):
            print(f"  📄 Fetching content from: {result['title']}")
            url = result["url"]
            if url:
                content = await self.fetch_webpage_content(url)
                if content and not content.startswith("Error") and not content.startswith("Failed"):
                    content_pieces.append({
                        "title": result["title"],
                        "url": url,
                        "content": content
                    })
        
        if not content_pieces:
            return "I found some resources online, but couldn't extract useful content. Please check official Infoblox documentation for accurate information."
        
        # Combine all content into a comprehensive context
        context = "\n\n".join([
            f"Source: {piece['title']} ({piece['url']})\n\n{piece['content']}"
            for piece in content_pieces
        ])
        
        # Generate a response using the online content
        system_msg = """You are a helpful assistant that provides accurate information about Infoblox products and services.
        Use ONLY the provided context to answer the question. If the information isn't in the context, say so clearly.
        Format your response to be clear and well-structured. Always cite sources at the end of your response."""
        
        user_msg = f"""
        The user asked: "{query}"
        
        Initial response (if incomplete or insufficient): "{initial_answer or ''}"
        
        Use the following context from online sources to provide a more comprehensive answer:
        
        {context}
        """
        
        try:
            response = await azure_client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            return f"I encountered an error while processing online information: {str(e)}. Please try again or check official Infoblox documentation."

async def main():
    """Main entry point for the supervisor agent."""
    # Create the supervisor agent
    supervisor = SupervisorAgent()
    
    print("\n🤖 Welcome to the AI Assistant! I can help with various requests.")
    print("=" * 70)
    print("I can answer questions about:")
    print("- Products, resources, and documentation")
    print("- Learning recommendations from LinkedIn Learning")
    print("- Organization structure, employees, and managers")
    print("- Finding people working on specific topics or projects")
    print("- Workplace communication and the 'no jerks' policy")
    print("- Employee onboarding, first day tasks, and required tools")
    print("=" * 70)
    
    # Main conversation loop
    while True:
        # Get user input
        user_input = input("\n💬 How can I help you today? (or type 'exit' to quit): ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\n👋 Goodbye! Have a great day!")
            break
        
        try:
            # Route the query to the appropriate agent
            await supervisor.route_query(user_input)
        except Exception as e:
            print(f"\n⚠️ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())