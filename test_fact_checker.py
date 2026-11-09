from agents.research_agent import ResearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.fact_checker import FactCheckerAgent


# Initialize all three agents
research_agent = ResearchAgent()
analysis_agent = AnalysisAgent()
fact_checker = FactCheckerAgent()


# Research topic
topic = "Latest developments in Generative AI"


# STEP 1: RESEARCH
print("\n========== STEP 1: RESEARCH ==========")

research_results = research_agent.research(topic)


# STEP 2: ANALYSIS
print("\n========== STEP 2: ANALYSIS ==========")

analysis_results = analysis_agent.analyze(
    topic,
    research_results
)

# Convert Gemini response into readable text
if isinstance(analysis_results, list):
    analysis_text = "\n".join(
        item["text"]
        for item in analysis_results
        if item.get("type") == "text"
    )
else:
    analysis_text = analysis_results


# STEP 3: FACT CHECKING
print("\n========== STEP 3: FACT CHECKING ==========")

fact_check_results = fact_checker.fact_check(
    topic,
    research_results,
    analysis_text
)


# DISPLAY FINAL RESULTS
print("\n========== FINAL FACT-CHECK REPORT ==========")

if isinstance(fact_check_results, list):
    for item in fact_check_results:
        if item.get("type") == "text":
            print(item["text"])
else:
    print(fact_check_results)


print("\n========== ALL THREE AGENTS COMPLETED ==========")