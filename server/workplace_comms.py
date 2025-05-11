#!/usr/bin/env python3
# workplace_comms.py - Agent to help with workplace communication following the "no jerks" policy

import asyncio
from typing import Dict, List, Any
from azure_wrapper import init_azure_openai

# This will be initialized by the supervisor
azure_client = None
deployment = None

class WorkplaceCommsAgent:
    """
    Agent that helps with workplace communication, especially for difficult conversations,
    following Infoblox's "no jerks" policy to ensure interactions are respectful and compassionate.
    """
    
    def __init__(self):
        """Initialize the workplace communication agent."""
        self.principles = [
            "Assume positive intent",
            "Focus on the issue, not the person",
            "Use 'I' statements instead of 'you' statements",
            "Practice active listening",
            "Be specific about behaviors rather than making generalizations",
            "Acknowledge others' perspectives",
            "Offer solutions, not just complaints",
            "Express gratitude",
            "Choose appropriate timing and setting for difficult conversations",
            "Follow up after difficult conversations"
        ]
        
    async def generate_communication_advice(self, query: str) -> str:
        """
        Generate advice for workplace communication situations.
        
        Args:
            query: The user's question about a workplace communication situation
            
        Returns:
            Advice for handling the situation respectfully and effectively
        """
        prompt = f"""
        As a workplace communication advisor following the "no jerks" policy at Infoblox, help the user 
        communicate effectively in the situation they've described. The "no jerks" policy promotes 
        treating colleagues with compassion and respect in all interactions.

        User situation: {query}

        When formulating your response, consider these principles:
        {', '.join(self.principles)}

        Provide specific, actionable advice that:
        1. Acknowledges the challenge
        2. Suggests respectful language and approaches
        3. Offers 2-3 conversation starters or templates
        4. Explains how this approach aligns with the "no jerks" policy

        Format your response conversationally but with clear, step-by-step guidance.
        """
        
        messages = [
            {"role": "system", "content": "You are a workplace communication advisor helping employees have difficult conversations with compassion and respect."},
            {"role": "user", "content": prompt}
        ]
        
        response = await azure_client.chat.completions.create(
            model=deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()

async def handle_workplace_query(query: str) -> str:
    """
    Handle a workplace communication query and return advice.
    
    Args:
        query: The user's question about a workplace communication situation
        
    Returns:
        Formatted advice for handling the situation
    """
    agent = WorkplaceCommsAgent()
    advice = await agent.generate_communication_advice(query)
    
    formatted_response = f"""
🤝 Workplace Communication Advice:
-------------------------------
{advice}
"""
    return formatted_response