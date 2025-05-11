from serpapi.google_search import GoogleSearch
from azure_wrapper import init_azure_openai
import asyncio

# Replace with your SerpAPI key
serpapi_key = "a2085f7720abb76cf0561d73b579330fb38f91ceee5b9f9034741398ffa57a45"

async def enhance_course_info(course_title, course_link):
    """Use Azure OpenAI to generate enhanced information about a LinkedIn course."""
    client, deployment = init_azure_openai()
    
    prompt = f"""
    Based on the LinkedIn Learning course title "{course_title}" and link {course_link},
    provide a brief 2-3 sentence description of what skills someone might learn in this course,
    the potential difficulty level, and who might benefit from taking it.
    Keep your response concise and informative.
    """
    
    response = await client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are a helpful AI that provides concise, accurate information about educational content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    return response.choices[0].message.content.strip()

def search_linkedin_courses(user_query):
    search = GoogleSearch({
        "q": f"site:linkedin.com/learning {user_query}",
        "api_key": serpapi_key
    })
    results = search.get_dict()

    output = []
    if "organic_results" in results:
        for res in results["organic_results"][:3]:  # Top 3
            output.append({
                "title": res['title'],
                "link": res['link']
            })
    else:
        output.append({"error": "❌ No courses found."})
    return output

async def process_courses(courses):
    """Process courses to add AI-enhanced descriptions."""
    enhanced_courses = []
    
    for course in courses:
        if "error" in course:
            enhanced_courses.append(course["error"])
            continue
            
        try:
            ai_description = await enhance_course_info(course["title"], course["link"])
            formatted_output = f"📚 {course['title']}\n🔗 {course['link']}\nℹ️ {ai_description}"

            enhanced_courses.append(formatted_output)
        except Exception as e:
            enhanced_courses.append(f"- {course['title']}: {course['link']}\n  ⚠️ Could not enhance: {str(e)}")
    
    return enhanced_courses

async def chatbot_async():
    print("🤖 Enhanced LinkedIn Learning Course Bot (Powered by SerpAPI + Azure OpenAI)")
    while True:
        user_query = input("\n💬 What do you want to learn? ")
        if user_query.lower() in {"exit", "quit"}:
            print("👋 Bye!")
            break

        print("\n🔎 Finding and analyzing LinkedIn Learning courses...\n")
        courses = search_linkedin_courses(user_query)
        
        if any("error" in course for course in courses):
            for course in courses:
                if "error" in course:
                    print(course["error"])
            continue
            
        enhanced_courses = await process_courses(courses)
        
        for course in enhanced_courses:
            print(course)
            print("-" * 60)

def chatbot():
    """Entry point for the chatbot."""
    asyncio.run(chatbot_async())

if __name__ == "__main__":
    chatbot()
