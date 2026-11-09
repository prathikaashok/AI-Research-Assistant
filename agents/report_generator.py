import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# Load environment variables
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(BASE_DIR, ".env"))


class ReportGenerator:

    def __init__(self):

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("Gemini API key not found!")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key
        )

        self.reports_dir = os.path.join(
            BASE_DIR, "reports"
        )

        os.makedirs(self.reports_dir, exist_ok=True)

    # Convert Gemini response into readable text
    def extract_text(self, content):

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            return "\n".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict)
                and item.get("type") == "text"
            )

        return str(content)

    # Generate an AI-powered executive summary
    def generate_summary(self, topic, analysis):

        prompt = f"""
        You are a professional research report writer.

        Research Topic: {topic}

        Research Analysis:
        {analysis}

        Write a professional executive summary.

        Include:
        1. What the research is about.
        2. Three to five major findings.
        3. Important developments.
        4. Key opportunities or implications.
        5. Important limitations.

        Requirements:
        - Use clear professional language.
        - Keep it between 150 and 250 words.
        - Only use information from the supplied analysis.
        - Do not invent facts or statistics.
        """

        response = self.llm.invoke(prompt)

        return self.extract_text(response.content)

    def generate_report(
        self,
        topic,
        research_data,
        analysis,
        fact_check
    ):

        print("\nReport Generator is creating your report...")

        # Generate executive summary
        print("\nGenerating AI Executive Summary...")

        executive_summary = self.generate_summary(
            topic,
            analysis
        )

        # Prepare source references
        sources = ""

        for index, result in enumerate(
            research_data, start=1
        ):

            sources += f"""
### Source {index}

**Title:** {result.get('title', 'Unknown')}

**URL:** {result.get('url', 'Not available')}

**Information:** {result.get('content', 'Not available')}

---
"""

        # Generate complete report
        report = f"""
# AI RESEARCH REPORT

## Research Topic
{topic}

## Generated On
{datetime.now().strftime('%d %B %Y, %I:%M %p')}

---

# 1. Executive Summary

{executive_summary}

---

# 2. Research Findings

{sources}

# 3. Detailed Analysis

{analysis}

# 4. Fact-Checking Results

{fact_check}

# 5. Conclusion

This report combines information collected from web sources
with AI-generated analysis and source-based fact-checking.

The findings should be independently verified before being
used for important decisions.

---

## End of Report

Generated using Multi-Agent AI Research Assistant.
"""

        # Create a safe filename
        safe_topic = "".join(
            character if character.isalnum() else "_"
            for character in topic
        )

        filename = f"{safe_topic[:60]}_report.md"

        report_path = os.path.join(
            self.reports_dir,
            filename
        )

        # Save report
        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(report)

        print("\nResearch report generated successfully!")

        print("Report saved at:", report_path)

        return report