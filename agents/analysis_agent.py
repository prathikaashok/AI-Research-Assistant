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
            google_api_key=api_key,
            temperature=0.2
        )

    def analyze(self, topic, research_data):

        if not research_data:
            raise ValueError("No research data available for analysis.")

        print("\nAnalysis Agent is analyzing the research...")

        # Prepare research information with source IDs
        research_sections = []

        for index, result in enumerate(research_data, start=1):

            title = result.get("title", "Unknown Title")
            url = result.get("url", "URL unavailable")
            content = result.get("content", "")

            research_sections.append(
                f"""
SOURCE ID: [S{index}]

Title: {title}

URL: {url}

Content:
{content}
"""
            )

        research_text = "\n".join(research_sections)

        # Create evidence-based analysis prompt
        prompt = f"""
You are a professional AI research analyst.

Research Topic:
{topic}

Your task is to produce an evidence-based research analysis
using ONLY the supplied research sources.

RESEARCH TASKS:

1. Identify the 3-5 most important findings.
2. Identify common themes across the sources.
3. Explain important technological developments.
4. Identify potential opportunities and implications.
5. Identify limitations, uncertainties and missing information.
6. Explain areas where different sources provide conflicting
   information.
7. Provide a balanced conclusion.

SOURCE VERIFICATION REQUIREMENTS:

- Assign source references to important factual claims.
- Use source IDs exactly as provided, such as [S1] or [S2].
- Do not invent source IDs, URLs or references.
- Only state facts explicitly supported by source content.
- Do not add technical specifications that are absent
  from the supplied sources.
- Do not invent statistics, dates, product names,
  model versions or performance improvements.
- If a detail is not explicitly supported, identify it
  as unverified rather than presenting it as fact.
- Distinguish direct evidence from your own interpretation.
- If only one source supports a claim, do not describe
  it as independently confirmed by multiple sources.
- Do not treat repeated claims from copied press releases
  as independent confirmation.

OUTPUT STRUCTURE:

# Research Analysis

## 1. Most Important Findings

Present 3-5 findings with supporting source IDs.

## 2. Common Themes

Explain recurring patterns across the research sources.

## 3. Major Technological Developments

Describe important developments with supporting source IDs.

## 4. Opportunities and Implications

Discuss potential applications and industry implications.
Clearly distinguish evidence from interpretation.

## 5. Limitations and Verification Gaps

Identify unsupported details, missing evidence and
limitations in the available research.

## 6. Conclusion

Provide a balanced conclusion based on the evidence.

WRITING REQUIREMENTS:

- Use professional research-report language.
- Avoid unnecessary repetition.
- Be precise and objective.
- Do not exaggerate findings.
- Do not present predictions as established facts.
- Do not invent information to fill gaps.

Research Sources:

{research_text}

Return the complete research analysis in Markdown.
"""

        # Generate analysis using Gemini
        response = self.llm.invoke(prompt)

        print("\nAnalysis completed successfully!")

        return response.content