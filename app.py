import streamlit as st
from workflow.graph import ResearchWorkflow


# -----------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide"
)


# -----------------------------------
# 2. APPLICATION HEADER
# -----------------------------------

st.title("🔬 Multi-Agent AI Research Assistant")

st.markdown(
    """
    Research smarter with AI.

    This application uses multiple AI agents to research,
    analyse, fact-check and generate detailed research reports.
    """
)

st.divider()


# -----------------------------------
# 3. RESEARCH INPUT
# -----------------------------------

st.subheader("Start Your Research")

topic = st.text_input(
    "Enter your research topic",
    placeholder="Example: Latest developments in Generative AI"
)


# -----------------------------------
# 4. START RESEARCH
# -----------------------------------

if st.button("🚀 Start Research", type="primary"):

    if not topic.strip():

        st.warning("Please enter a research topic.")

    else:

        try:

            with st.spinner(
                "AI agents are working on your research..."
            ):

                research_workflow = ResearchWorkflow()

                result = research_workflow.run(topic)

            st.success("Research completed successfully!")

            # -----------------------------------
            # 5. DISPLAY RESEARCH RESULTS
            # -----------------------------------

            st.divider()

            st.header("📚 Research Results")

            with st.expander("View Collected Sources"):

                for index, source in enumerate(
                    result["research_data"], start=1
                ):

                    st.subheader(f"Source {index}")

                    st.write("**Title:**", source["title"])

                    st.write("**URL:**", source["url"])

                    st.write("**Content:**", source["content"])

                    st.divider()

            # -----------------------------------
            # 6. DISPLAY ANALYSIS
            # -----------------------------------

            st.header("🧠 AI Analysis")

            st.markdown(result["analysis"])

            # -----------------------------------
            # 7. FACT CHECKING
            # -----------------------------------

            st.header("🔍 Fact-Checking Results")

            st.markdown(result["fact_check"])

            # -----------------------------------
            # 8. DOWNLOAD REPORT
            # -----------------------------------

            st.header("📄 Research Report")

            st.download_button(
                label="⬇️ Download Research Report",
                data=result["report"],
                file_name="AI_Research_Report.md",
                mime="text/markdown"
            )

            st.success("Your report is ready to download!")

        except Exception as e:

            st.error(f"An error occurred: {str(e)}")