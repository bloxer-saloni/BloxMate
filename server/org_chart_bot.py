#!/usr/bin/env python3
# org_chart_bot.py - Agent for looking up employee information from org_chart.csv
import asyncio
import csv
from typing import Optional, Dict, List, Tuple
from agents import Agent, Runner, function_tool
from azure_wrapper import init_azure_openai
import pypdf
import os
import re

# Global variable to store the org chart data
ORG_CHART_DATA = {}

# Global variable to store the weekly update data
WEEKLY_UPDATE_DATA = []

def load_org_chart(file_path: str = "org_chart.csv") -> Dict:
    """
    Load the organization chart data from a CSV file
    
    Args:
        file_path: Path to the CSV file containing org chart data
    
    Returns:
        Dictionary with employee names as keys and their information as values
    """
    data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data[row['name'].lower()] = {
                    'name': row['name'],
                    'title': row['title'],
                    'manager': row['manager']
                }
        print(f"Successfully loaded {len(data)} employees from org chart")
        return data
    except Exception as e:
        print(f"Error loading org chart data: {e}")
        return {}

def load_weekly_updates(file_path: str = "Data Science Weekly Status Update.pdf") -> List[Dict]:
    """
    Load the weekly update data from the PDF file
    
    Args:
        file_path: Path to the PDF file containing weekly updates
    
    Returns:
        List of dictionaries with engineer names and their updates
    """
    updates = []
    try:
        # Load the PDF
        pdf = pypdf.PdfReader(file_path)
        all_text = ""
        
        # Extract text from all pages
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"
        
        # Split by engineer entries (looking for name followed by projects)
        # This regex pattern looks for entries that start with an engineer name
        # and captures their work updates until the next engineer entry
        engineer_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]*)\s+(.*?)(?=\n[A-Z][a-z]+\s+[A-Z][a-z]*\s+|\Z)'
        
        # Find all matches in the text
        matches = re.finditer(engineer_pattern, all_text, re.DOTALL)
        
        for match in matches:
            name = match.group(1).strip()
            content = match.group(2).strip()
            
            # Further split content into work items
            # Extract completed work and targets
            completed_work = ""
            target_work = ""
            
            # Look for completed/target sections
            completed_match = re.search(r'(.*?)(?:Target for next week)', content, re.DOTALL)
            if completed_match:
                completed_work = completed_match.group(1).strip()
                target_match = re.search(r'Target for next week\s+(.*)', content, re.DOTALL)
                if target_match:
                    target_work = target_match.group(1).strip()
            else:
                # If pattern not found, use all content as completed work
                completed_work = content
            
            updates.append({
                "name": name,
                "completed_work": completed_work,
                "target_work": target_work,
                "full_content": content
            })
        
        print(f"Successfully loaded updates for {len(updates)} engineers from weekly update")
        return updates
    except Exception as e:
        print(f"Error loading weekly update data: {e}")
        return []

def search_weekly_updates(query: str) -> List[Dict]:
    """
    Search the weekly updates for relevant information
    
    Args:
        query: The search query
    
    Returns:
        List of relevant updates
    """
    query_terms = query.lower().split()
    results = []
    
    for update in WEEKLY_UPDATE_DATA:
        content = update["full_content"].lower()
        name = update["name"].lower()
        
        # Calculate a simple relevance score based on term frequency
        score = sum(1 for term in query_terms if term in content)
        
        # If any terms match, add to results
        if score > 0:
            results.append({
                "name": update["name"],
                "score": score,
                "content": update["full_content"],
                "completed_work": update["completed_work"],
                "target_work": update["target_work"]
            })
    
    # Sort by relevance score (highest first)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

@function_tool
async def lookup_employee(name: str) -> str:
    """
    Look up information about an employee by name
    
    Args:
        name: The name of the employee to look up
    
    Returns:
        Information about the employee including their job title and manager
    """
    name_lower = name.lower()
    
    # Check for exact match
    if name_lower in ORG_CHART_DATA:
        employee = ORG_CHART_DATA[name_lower]
        
        # Create response with job title and manager
        response = f"{employee['name']} has the job title: {employee['title']}"
        
        if employee['manager']:
            manager_info = ORG_CHART_DATA.get(employee['manager'].lower(), {})
            manager_title = manager_info.get('title', 'Unknown Title') if manager_info else 'Unknown Title'
            response += f"\nTheir manager is {employee['manager']} ({manager_title})"
        else:
            response += "\nThey do not have a manager (top of organization)"
            
        return response
    
    # Try partial matches if exact match fails
    partial_matches = [emp for name_key, emp in ORG_CHART_DATA.items() 
                      if name_lower in name_key]
    
    if partial_matches:
        if len(partial_matches) == 1:
            # Single partial match
            employee = partial_matches[0]
            response = f"{employee['name']} has the job title: {employee['title']}"
            
            if employee['manager']:
                manager_info = ORG_CHART_DATA.get(employee['manager'].lower(), {})
                manager_title = manager_info.get('title', 'Unknown Title') if manager_info else 'Unknown Title'
                response += f"\nTheir manager is {employee['manager']} ({manager_title})"
            else:
                response += "\nThey do not have a manager (top of organization)"
                
            return response
        else:
            # Multiple partial matches
            matches = [emp['name'] for emp in partial_matches]
            return f"Found multiple people matching '{name}': {', '.join(matches)}. Please specify which one you're looking for."
    
    return f"Could not find anyone named '{name}' in the organization chart."

@function_tool
async def list_employees_under_manager(manager_name: str) -> str:
    """
    List all employees who report to a specific manager
    
    Args:
        manager_name: The name of the manager
    
    Returns:
        List of employees reporting to the specified manager
    """
    manager_name_lower = manager_name.lower()
    
    # First check if the manager exists
    manager_key = None
    for name_key, emp in ORG_CHART_DATA.items():
        if manager_name_lower in name_key:
            manager_key = emp['name']
            break
    
    if not manager_key:
        return f"Could not find a manager named '{manager_name}' in the organization chart."
    
    # Find all employees reporting to this manager
    direct_reports = []
    for emp in ORG_CHART_DATA.values():
        if emp['manager'] == manager_key:
            direct_reports.append(f"{emp['name']} ({emp['title']})")
    
    if direct_reports:
        return f"{manager_key} manages {len(direct_reports)} employees:\n" + "\n".join(direct_reports)
    else:
        return f"{manager_key} does not have any direct reports in the organization chart."

@function_tool
async def find_people_working_on(topic: str) -> str:
    """
    Find people working on a specific topic based on weekly updates
    
    Args:
        topic: The topic or project to search for
    
    Returns:
        List of people working on the specified topic and relevant details
    """
    results = search_weekly_updates(topic)
    
    if not results:
        return f"I couldn't find anyone working on '{topic}' in the weekly updates."
    
    response = f"Found {len(results)} people working on topics related to '{topic}':\n\n"
    
    for result in results[:5]:  # Limit to top 5 matches
        response += f"📊 {result['name']}:\n"
        
        # Extract relevant snippets containing the search terms
        snippets = []
        for term in topic.lower().split():
            content = result['content'].lower()
            term_pos = content.find(term)
            if term_pos >= 0:
                start = max(0, term_pos - 50)
                end = min(len(content), term_pos + 50)
                
                # Find a good starting point at word boundary
                while start > 0 and content[start] != ' ' and content[start] != '\n':
                    start -= 1
                
                # Find a good ending point at word boundary
                while end < len(content) - 1 and content[end] != ' ' and content[end] != '\n':
                    end += 1
                
                snippet = "..." + content[start:end].strip() + "..."
                snippets.append(snippet)
        
        if snippets:
            response += "  Relevant work: " + "\n  ".join(snippets[:2]) + "\n\n"
        else:
            # If no good snippets, show the completed work
            response += f"  Completed work: {result['completed_work'][:150]}...\n\n"
    
    return response

@function_tool
async def who_to_contact_for(topic: str) -> str:
    """
    Find the best person to contact for information on a specific topic
    
    Args:
        topic: The topic to get information about
    
    Returns:
        The best person to contact and their relevance to the topic
    """
    results = search_weekly_updates(topic)
    
    if not results:
        return f"I couldn't find anyone with expertise on '{topic}' in the weekly updates."
    
    # Get the most relevant person
    best_match = results[0]
    
    response = f"For information about '{topic}', you should contact:\n\n"
    response += f"👤 {best_match['name']}\n\n"
    
    # Extract relevant snippets containing the search terms
    snippets = []
    for term in topic.lower().split():
        content = best_match['content'].lower()
        term_pos = content.find(term)
        if term_pos >= 0:
            start = max(0, term_pos - 50)
            end = min(len(content), term_pos + 50)
            
            # Find word boundaries
            while start > 0 and content[start] != ' ' and content[start] != '\n':
                start -= 1
            
            while end < len(content) - 1 and content[end] != ' ' and content[end] != '\n':
                end += 1
            
            snippet = "..." + content[start:end].strip() + "..."
            snippets.append(snippet)
    
    if snippets:
        response += "Their recent work relevant to this topic includes:\n" + "\n".join(snippets[:2])
    else:
        # If no good snippets, show the completed work
        response += f"Their recent work includes:\n{best_match['completed_work'][:200]}..."
    
    # If we have org chart data for this person, include their title
    name_key = best_match['name'].lower()
    for emp_name, emp_data in ORG_CHART_DATA.items():
        if name_key in emp_name:
            response += f"\n\nTheir title is: {emp_data['title']}"
            break
    
    return response

async def main():
    # Load the org chart data
    global ORG_CHART_DATA
    ORG_CHART_DATA = load_org_chart()
    
    if not ORG_CHART_DATA:
        print("Error: Could not load organization chart data. Please check if org_chart.csv exists.")
        return
    
    # Load the weekly update data
    global WEEKLY_UPDATE_DATA
    WEEKLY_UPDATE_DATA = load_weekly_updates()
    
    # Create the agent with the employee lookup tools
    client, deployment = init_azure_openai()
    
    # Create the agent with the employee lookup tools
    agent = Agent(
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
        tools=[lookup_employee, list_employees_under_manager, find_people_working_on, who_to_contact_for]
    )
    
    print("OrgChart and Project Assistant initialized. Type 'exit' or 'quit' to end the session.")
    print("=" * 60)
    print("Example queries:")
    print("- What is Mark Peterson's job title?")
    print("- Who is Vidhi Vazirani's manager?")
    print("- Who reports to Sastry Varanasi?")
    print("- Find someone working on certifications")
    print("- Who should I contact for information on security logs?")
    print("=" * 60)
    
    # Main conversation loop
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Agent: Goodbye! Have a great day!")
            break
        
        try:
            # Process the user input and get a response using Runner
            result = await Runner.run(agent, user_input)
            
            # Display the response
            print(f"\nAgent: {result.final_output}")
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())