import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# Load environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class FactCheckerAgent:

    def __init__(self):

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("Gemini API key not found!")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key,
            timeout=60,
            max_retries=1,
            temperature=0.2
        )

    def fact_check(self, topic, research_data, analysis):

        print("\nFact-Checking Agent is checking the research...")

        start_time = time.time()

        try:

            # Prepare original research sources
            sources = ""

            for index, result in enumerate(research_data, start=1):

                content = result.get("content", "")

                # Limit source content to avoid unnecessarily large prompts
                content = content[:5000]

                sources += f"""
Source {index}
Title: {result.get('title', 'Unknown')}
URL: {result.get('url', 'Unknown')}
Content: {content}
"""

            # Prepare fact-checking prompt
            prompt = f"""
You are a professional fact-checking assistant.

Research Topic: {topic}

Original Research Sources:
{sources}

AI Generated Analysis:
{analysis}

Your tasks:

1. Identify important factual claims in the analysis.
2. Compare each claim against the supplied sources.
3. Identify claims supported by the sources.
4. Identify claims that are unsupported.
5. Identify conflicting or potentially misleading claims.
6. Mention which source supports each claim when possible.
7. Highlight information that needs independent verification.

IMPORTANT:
- Do not invent evidence.
- Do not treat unsupported claims as verified.
- The supplied sources may themselves be inaccurate.
- Clearly distinguish supported, unsupported and conflicting claims.

Present the result using clear headings.

End with an overall reliability assessment.
"""

            print("Sending fact-checking request to Gemini...")

            response = self.llm.invoke(prompt)

            result = response.content

            elapsed_time = round(time.time() - start_time, 2)

            print("\nFact-checking completed successfully!")
            print(f"Fact-checking time: {elapsed_time} seconds")

            return result

        except Exception as e:

            print("\nFact-checking failed!")
            print(f"Error: {str(e)}")

            raise RuntimeError(
                f"Fact-checking failed: {str(e)}"
            ) from e