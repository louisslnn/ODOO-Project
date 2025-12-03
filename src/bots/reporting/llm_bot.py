import os
import google.generativeai as genai
from loguru import logger

class LLMBot:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY missing in .env file")
            self.model = None
            return

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def ask_finance_advisor(self, user_question, financial_context):
        """Sends financial data and user question to the LLM."""
        if not self.model:
            return "Error: AI not configured."

        # System Prompt in English
        prompt = f"""
        You are an Expert AI Financial Advisor (CFO) for a company.
        Your tone is professional, concise, and helpful.

        HERE IS THE REAL-TIME FINANCIAL DATA (CONTEXT):
        {financial_context}

        INSTRUCTIONS:
        1. Use ONLY the context provided above to answer.
        2. If the answer is not in the context, state that you do not know.
        3. If anomalies are detected (Audit), mention them as a priority.
        4. Answer the user's question below.

        USER QUESTION:
        "{user_question}"
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return "Sorry, I am unable to process this request at the moment."