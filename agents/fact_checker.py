import os
import time

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# ==================================================
# PROJECT CONFIGURATION
# ==================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(BASE_DIR, ".env"))


class FactCheckerAgent:

    def __init__(self):

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("Gemini API key not found!")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key,
            temperature=0.2,
            timeout=60,
            max_retries=1
        )

        # Manual retry configuration
        self.max_attempts = 4
        self.initial_delay = 5

        print("Fact Checker Agent initialized successfully!")

    # ==================================================
    # RETRY ERROR DETECTION
    # ==================================================

    def _is_retryable_error(self, error):

        error_message = str(error).upper()

        retryable_codes = [
            "429",
            "500",
            "502",
            "503",
            "504",
            "UNAVAILABLE",
            "RESOURCE_EXHAUSTED",
            "INTERNAL"
        ]

        return any(
            code in error_message
            for code in retryable_codes
        )

    # ==================================================
    # GEMINI INVOCATION WITH RETRIES
    # ==================================================

    def _invoke_with_retry(self, prompt):

        for attempt in range(
            1,
            self.max_attempts + 1
        ):

            try:

                print(
                    f"Fact-checking attempt "
                    f"{attempt}/{self.max_attempts}"
                )

                response = self.llm.invoke(prompt)

                return response.content

            except Exception as error:

                print(
                    f"Fact-checking error: {error}"
                )

                if (
                    attempt == self.max_attempts
                    or not self._is_retryable_error(error)
                ):

                    raise RuntimeError(
                        "Fact-checking failed after "
                        f"{attempt} attempt(s): {error}"
                    ) from error

                delay = (
                    self.initial_delay
                    * (2 ** (attempt - 1))
                )

                print(
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)

        raise RuntimeError(
            "Fact-checking could not be completed."
        )

    # ==================================================
    # FACT-CHECKING
    # ==================================================

    def fact_check(
        self,
        topic,
        research_data,
        analysis
    ):

        print("\nFact Checker Agent is verifying findings...")

        # Prepare research sources
        sources = ""

        for index, result in enumerate(
            research_data,
            start=1
        ):

            title = result.get(
                "title",
                "Unknown"
            )

            url = result.get(
                "url",
                "Not available"
            )

            content = result.get(
                "content",
                ""
            )

            # Limit source content to avoid excessively
            # large prompts.
            content = str(content)[:5000]

            sources += f"""
Source {index}

Title: {title}

URL: {url}

Content:
{content}

----------------------------------------
"""

        # Build fact-checking prompt
        prompt = f"""
You are an experienced research fact-checking analyst.

Your task is to critically evaluate the claims made in
an AI-generated research analysis using the supplied
research sources.

RESEARCH TOPIC:
{topic}

RESEARCH ANALYSIS:
{analysis}

AVAILABLE RESEARCH SOURCES:
{sources}

FACT-CHECKING INSTRUCTIONS:

1. Identify the important factual claims in the analysis.

2. Compare each claim against the supplied research sources.

3. Classify claims using these categories:

   - SUPPORTED: Evidence from the supplied sources
     directly supports the claim.

   - PARTIALLY SUPPORTED: The sources support only
     part of the claim or provide incomplete evidence.

   - UNSUPPORTED: The supplied sources do not provide
     sufficient evidence for the claim.

   - CONFLICTING: The supplied sources contain
     contradictory information.

4. Include source titles and URLs when providing evidence.

5. Identify misleading statements, unsupported
   statistics, and exaggerated conclusions.

6. Do not invent evidence, statistics, quotations,
   references, or source URLs.

7. Clearly distinguish between:
   - Information supported by the supplied sources.
   - Information that cannot be verified.
   - Information that requires independent verification.

8. Do not treat the absence of evidence as proof
   that a claim is false.

9. Provide an overall assessment of the reliability
   of the research analysis.

OUTPUT FORMAT:

# Fact-Checking Report

## 1. Overview

Briefly describe the fact-checking process.

## 2. Claim Verification

For each important claim, provide:

- Claim:
- Verification Status:
- Supporting Evidence:
- Source:
- Explanation:

## 3. Unsupported or Uncertain Claims

Identify claims that lack sufficient evidence.

## 4. Conflicting Information

Explain any contradictions found between sources.

If none are found, explicitly state that.

## 5. Potentially Misleading Statements

Identify exaggerated or misleading claims.

If none are found, explicitly state that.

## 6. Overall Reliability Assessment

Provide an overall assessment of the analysis.

Use one of these labels:

- High Reliability
- Moderate Reliability
- Low Reliability

Explain your assessment using the available evidence.

IMPORTANT:

Only use the supplied research sources.
Never fabricate evidence.
Be objective, critical, and transparent about limitations.
"""

        # Invoke Gemini with retry handling
        result = self._invoke_with_retry(prompt)

        print("\nFact-checking completed successfully!")

        return result