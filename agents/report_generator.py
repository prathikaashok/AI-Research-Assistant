import os
import re
from datetime import datetime

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# ==================================================
# PROJECT CONFIGURATION
# ==================================================

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
            BASE_DIR,
            "reports"
        )

        os.makedirs(
            self.reports_dir,
            exist_ok=True
        )

    # ==================================================
    # TEXT EXTRACTION
    # ==================================================

    def extract_text(self, content):

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):

            extracted = []

            for item in content:

                if isinstance(item, dict):

                    if item.get("type") == "text":
                        extracted.append(
                            item.get("text", "")
                        )

                elif isinstance(item, str):
                    extracted.append(item)

            return "\n".join(extracted).strip()

        if isinstance(content, dict):
            return str(content)

        return str(content)

    # ==================================================
    # FORMAT CONTENT
    # ==================================================

    def format_section(self, content):

        text = self.extract_text(content)

        if not text:
            return "No information available."

        return text

    # ==================================================
    # CLEAN SOURCE CONTENT
    # ==================================================

    def clean_source_content(self, content):

        text = self.extract_text(content)

        if not text:
            return ""

        # Normalize whitespace.
        text = re.sub(r"\s+", " ", text).strip()

        # Remove common website noise.
        noise_patterns = [
            r"(?i)accept all cookies",
            r"(?i)cookie preferences",
            r"(?i)cookie policy",
            r"(?i)privacy policy",
            r"(?i)terms and conditions",
            r"(?i)subscribe to our newsletter",
            r"(?i)sign up for our newsletter",
            r"(?i)all rights reserved",
            r"(?i)manage cookies",
            r"(?i)we use cookies",
            r"(?i)consent preferences",
            r"(?i)skip to main content",
            r"(?i)jump to main content",
            r"(?i)back to top",
            r"(?i)image\s*\d+\s*:",
            r"(?i)figure\s*\d+\s*:",
            r"(?i)photo\s+by\s+[^.]+",
            r"(?i)image:\s*[^.]+",
            r"(?i)sign in to continue",
            r"(?i)subscribe now",
            r"(?i)read more articles",
            r"(?i)related articles",
            r"(?i)recommended articles",
        ]

        for pattern in noise_patterns:
            text = re.sub(pattern, "", text)

        # Remove navigation labels at the beginning.
        navigation_pattern = (
            r"^(?:(?:about us|home|menu|"
            r"subscribe|advertise|login|log in|"
            r"sign in|register|contact us|"
            r"careers|privacy|impressum|"
            r"skip to content|jump to content|"
            r"table of contents|search|"
            r"journals|technology|"
            r"advanced hub|online library)"
            r"[\s|•·›»\-]*)+"
        )

        text = re.sub(
            navigation_pattern,
            "",
            text,
            flags=re.IGNORECASE
        )

        # Remove repeated navigation phrases.
        repeated_navigation = [
            "About us",
            "Subscribe",
            "Advertise",
            "Privacy",
            "Impressum",
            "Wiley Online Library",
            "Advanced Hub",
            "Select Page",
            "Skip to content",
        ]

        for phrase in repeated_navigation:
            text = re.sub(
                re.escape(phrase),
                "",
                text,
                flags=re.IGNORECASE
            )

        # Remove excessive separators.
        text = re.sub(
            r"(?:\s*[|•·›»]\s*){2,}",
            " ",
            text
        )

        # Normalize whitespace again.
        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        return text

    # ==================================================
    # GENERATE EXECUTIVE SUMMARY
    # ==================================================

    def generate_summary(self, topic, analysis, fact_check):

        analysis_text = self.format_section(analysis)
        fact_check_text = self.format_section(fact_check)

        reliability_match = re.search(
            r"\*\*Label:\*\*\s*(High|Moderate|Low)\s+Reliability",
            fact_check_text,
            re.IGNORECASE
        )

        reliability_label = (
            reliability_match.group(1).capitalize()
            if reliability_match
            else "Not explicitly assigned"
        )

        prompt = f"""
You are an expert research report writer.

Create a clear, professional executive summary
for the following research topic.

TOPIC:
{topic}

RESEARCH ANALYSIS:
{analysis_text}

FACT-CHECK RESULTS:
{fact_check_text}

IMPORTANT INSTRUCTIONS:

1. Summarize the most important findings.
2. Clearly distinguish verified facts from interpretations.
3. Mention important limitations and uncertainties.
4. Do not introduce information that is absent
   from the supplied analysis.
5. Do not invent statistics, dates, or sources.
6. Preserve the fact-checker's conclusions.
7. Do not describe unsupported claims as verified.
8. Do not upgrade or downgrade the reliability rating.

The fact-checker's actual reliability label is:
{reliability_label} Reliability

Use exactly this label if you mention reliability.

Write a concise executive summary in professional
Markdown with approximately 3-5 paragraphs.
"""

        response = self.llm.invoke(prompt)

        return self.extract_text(response.content)


    # ==================================================
    # GENERATE SOURCE REGISTER
    # ==================================================

    def generate_source_register(self, research_data):

        if not research_data:
            return "No research sources were available."

        source_sections = []

        for index, result in enumerate(
            research_data,
            start=1
        ):

            if not isinstance(result, dict):
                continue

            title = result.get(
                "title",
                "Unknown"
            )

            url = result.get(
                "url",
                "Not available"
            )

            content = self.clean_source_content(
                result.get("content", "")
            )

            if len(content) > 500:
                content = (
                    content[:500].rsplit(" ", 1)[0]
                    + "..."
                )

            if not content:
                content = "No source excerpt available."

            gemini_score = result.get(
                "gemini_relevance_score"
            )

            overall_score = result.get(
                "final_score"
            )

            credibility_score = result.get(
                "credibility_score"
            )

            source_type = result.get(
                "source_type",
                "Not classified"
            )

            source_section = f"""
### Source {index}: {title}

- **URL:** {url}
- **Source Type:** {source_type}
- **Gemini Relevance Score:** {
    gemini_score if gemini_score is not None
    else "Not available"
}
- **Overall Weighted Score:** {
    overall_score if overall_score is not None
    else "Not available"
}
- **Credibility Score:** {
    credibility_score if credibility_score is not None
    else "Not available"
}

**Evidence Excerpt:**

{content}

---
"""

            source_sections.append(source_section)

        if not source_sections:
            return "No valid research sources were available."

        return "\n".join(source_sections)


    # ==================================================
    # GENERATE FINAL REPORT
    # ==================================================

    def generate_report(
        self,
        topic,
        research_data,
        analysis,
        fact_check
    ):

        print("\nGenerating executive summary...")

        summary = self.generate_summary(
            topic,
            analysis,
            fact_check
        )

        print("Formatting analysis...")

        analysis_text = self.format_section(
            analysis
        )

        fact_check_text = self.format_section(
            fact_check
        )

        print("Generating source register...")

        source_register = self.generate_source_register(
            research_data
        )

        current_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        safe_topic = re.sub(
            r'[<>:"/\\|?*]',
            "",
            topic
        ).strip()

        report = f"""# Research Report: {topic}

**Generated:** {current_time}

---

# 1. Executive Summary

{summary}

---

# 2. Research Analysis

{analysis_text}

---

# 3. Fact-Checking Results

{fact_check_text}

---

# 4. Source Register

{source_register}

---

# End of Report
"""

        filename = (
            safe_topic.replace(" ", "_")
            + "_report.md"
        )

        report_path = os.path.join(
            self.reports_dir,
            filename
        )

        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as report_file:

            report_file.write(report)

        print(
            f"\nReport successfully saved: {report_path}"
        )

        return report