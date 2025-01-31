from typing import Optional

from nemoguardrails.actions import action

@action(is_system_action=True)
async def check_blocked_terms(context: Optional[dict] = None):
    bot_response = context.get("bot_message")

    # A quick hard-coded list of proprietary terms. You can also read this from a file.
    proprietary_terms = ["proprietary", "proprietary1", "proprietary2"]

    for term in proprietary_terms:
        if term in bot_response.lower():
            print(F"THIS MESSAGE IS FROM THE CHECK_BLOCKED_TERMS ACTION, THE BOT RESPONSE CONTAINS THE TERM: {term} WHICH IS WHY YOU GET THE ANSWER: `I cannot talk about proprietary technology.`")
            return True

    return False