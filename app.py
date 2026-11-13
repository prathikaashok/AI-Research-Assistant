from pathlib import Path

import streamlit as st
from workflow.graph import ResearchWorkflow


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Multi-Agent AI Research Assistant",
    page_icon="🔬",
    layout="wide"
)


# ==========================================
# CONSTANTS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

REPORT_PATHS = [
    BASE_DIR / "reports" / "Latest_developments_in_Generative_AI_report.md",
    BASE_DIR / "reports" / "latest_development_in_generative_AI_report.md"
]


def load_sample_report():
    """Load an existing generated report for offline demonstration."""

    for report_path in REPORT_PATHS:
        if report_path.exists():
            return report_path.read_text(encoding="utf-8")

    return None


# ==========================================
# APPLICATION HEADER
# ==========================================

st.title("🔬 Multi-Agent AI Research Assistant")

st.markdown(
    """
    An AI-powered research application that uses multiple
    specialized agents to collect information, analyse findings,
    fact-check results and generate structured research reports.
    """
)

st.divider()


# ==========================================
# MODE SELECTION
# ==========================================

st.subheader("Choose Research Mode")

mode = st.radio(
    "Application Mode",
    ["Demo Mode", "Live Research Mode"],
    horizontal=True
)


# ==========================================
# DEMO MODE
# ==========================================

if mode == "Demo Mode":

    st.info(
        "Demo Mode: This displays a previously generated research "
        "report. No external API calls are made."
    )

    sample_report = load_sample_report()

    if sample_report:

        st.success("Sample research report loaded successfully!")

        st.header("📄 Research Report")

        st.markdown(sample_report)

        st.download_button(
            label="⬇️ Download Sample Research Report",
            data=sample_report,
            file_name="AI_Research_Demo_Report.md",
            mime="text/markdown"
        )

    else:

        st.error(
            "Sample report not found. Please check the reports folder."
        )


# ==========================================
# LIVE RESEARCH MODE
# ==========================================

else:

    st.info(
        "Live Mode: Runs the actual multi-agent research workflow "
        "using Tavily and Gemini APIs."
    )

    topic = st.text_input(
        "Enter your research topic",
        placeholder="Example: Latest developments in Generative AI"
    )

    if st.button("🚀 Start Live Research", type="primary"):

        if not topic.strip():

            st.warning("Please enter a research topic.")

        else:

            try:

                with st.spinner(
                    "Research, analysis, fact-checking and report "
                    "generation are in progress..."
                ):

                    research_workflow = ResearchWorkflow()

                    result = research_workflow.run(topic.strip())

                st.success("Research completed successfully!")

                st.divider()

                # Research results
                st.header("📚 Research Results")

                research_data = result.get("research_data", [])

                st.write(
                    f"Number of selected sources: {len(research_data)}"
                )

                with st.expander("View Collected Sources"):

                    for index, source in enumerate(
                        research_data, start=1
                    ):

                        st.subheader(f"Source {index}")

                        st.write(
                            "**Title:**",
                            source.get("title", "Untitled")
                        )

                        st.write(
                            "**URL:**",
                            source.get("url", "Not available")
                        )

                        st.write(
                            "**Content:**",
                            source.get("content", "No content available")
                        )

                        st.divider()

                # Analysis
                st.header("🧠 AI Analysis")

                st.markdown(
                    result.get("analysis", "No analysis available.")
                )

                # Fact checking
                st.header("🔍 Fact-Checking Results")

                st.markdown(
                    result.get("fact_check", "No fact-check results available.")
                )

                # Report
                st.header("📄 Research Report")

                report = result.get("report", "")

                if report:

                    st.download_button(
                        label="⬇️ Download Research Report",
                        data=report,
                        file_name="AI_Research_Report.md",
                        mime="text/markdown"
                    )

                else:

                    st.warning("The workflow did not generate a report.")

            except Exception as error:

                st.error(
                    "Live research could not be completed."
                )

                st.warning(
                    "This may be caused by temporary API availability, "
                    "rate limits or configuration issues."
                )

                with st.expander("Technical error details"):

                    st.code(str(error))


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Multi-Agent AI Research Assistant | "
    "Built using Python, Streamlit, LangGraph, Tavily and Gemini."
)
