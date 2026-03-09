from robot_sync_app.ports.llm_port import LLMPort


class SimpleLLMAdapter(LLMPort):
    def generate_reply(self, user_text: str, intent: str = "chat") -> str:
        if intent == "quiz":
            return f"Great try. Your answer was: {user_text}. Let's do the next question."
        return f"I heard you say: {user_text}. To infinity and beyond!"
