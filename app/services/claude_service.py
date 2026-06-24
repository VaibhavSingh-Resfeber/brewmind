from typing import Optional

from anthropic import Anthropic
from app.core.config import settings


def generate_recommendation(
    user_query: str,
    retrieved_cafes: list[dict],
    user_profile: Optional[dict] = None
) -> str:
    """
    Generate a personalized cafe recommendation using Claude.
    
    Args:
        user_query: The user's coffee/cafe preference question
        retrieved_cafes: List of cafe dictionaries from vector search
        user_profile: Optional user taste profile
        
    Returns:
        A conversational recommendation string from Claude
    """
    
    # Initialize Anthropic client (uses ANTHROPIC_API_KEY env var by default)
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    # System prompt
    system_prompt = """You are a knowledgeable Munich specialty coffee guide. 
You help people discover the perfect cafes for their taste and needs.

IMPORTANT RULES:
- ONLY recommend cafes from the provided list. NEVER invent or suggest cafes not in the list.
- Be conversational and warm, not like a search result list.
- If you don't know something or can't answer based on provided information, say so honestly.
- Consider the user's taste profile when making recommendations, if provided.
- Explain why each recommendation suits their preferences."""

    # Format retrieved cafes
    cafes_text = "AVAILABLE CAFES:\n\n"
    for cafe in retrieved_cafes:
        cafes_text += f"📍 {cafe.get('name', 'Unknown')}\n"
        if cafe.get('neighborhood'):
            cafes_text += f"   Neighborhood: {cafe['neighborhood']}\n"
        if cafe.get('roast_profile'):
            cafes_text += f"   Roast Profile: {cafe['roast_profile']}\n"
        if cafe.get('vibe'):
            cafes_text += f"   Vibe: {cafe['vibe']}\n"
        if cafe.get('brewing_methods'):
            cafes_text += f"   Brewing Methods: {', '.join(cafe['brewing_methods'])}\n"
        if cafe.get('good_for_working') is not None:
            cafes_text += f"   Good for Working: {'Yes' if cafe['good_for_working'] else 'No'}\n"
        if cafe.get('wifi') is not None:
            cafes_text += f"   WiFi: {'Yes' if cafe['wifi'] else 'No'}\n"
        cafes_text += "\n"
    
    # Build user message
    user_message = f"""User Question: {user_query}

{cafes_text}"""
    
    # Add user profile if available
    if user_profile:
        user_message += f"User Taste Profile:\n"
        for key, value in user_profile.items():
            user_message += f"- {key}: {value}\n"
    
    # Call Claude API
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    # Extract and return the response text
    return response.content[0].text
