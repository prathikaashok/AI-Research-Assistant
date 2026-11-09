import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# Load environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"))


class AnalysisAgent:

    def __init__(self):

        # Get Gemini API key
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("Gemini API key not found!")

        # Initialize Gemini
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key
        )

    def analyze(self, topic, research_data):

        if not research_data:
            raise ValueError("No research data available for analysis.")

        print("\nAnalysis Agent is analyzing the research...")

        # Prepare research information
        research_text = ""

        for index, result in enumerate(research_data, start=1):

            research_text += f"""
            Source {index}
            Title: {result['title']}
            URL: {result['url']}
            Content: {result['content']}
            """

        # Create analysis prompt
        prompt = f"""
        You are an expert AI research analyst.

        Research Topic: {topic}

        Analyse the following research information.

        Your tasks:

        1. Identify the most important findings.
        2. Identify common themes.
        3. Explain important developments.
        4. Identify potential opportunities.
        5. Mention limitations or missing information.
        6. Provide a clear conclusion.

        Use clear headings and professional language.

        Only use the information provided.
        Do not invent facts.

        Research Information:

        {research_text}
        """

        # Generate analysis using Gemini
        response = self.llm.invoke(prompt)

        print("\nAnalysis completed successfully!")

        return response.content