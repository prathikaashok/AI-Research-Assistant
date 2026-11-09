from agents.research_agent import ResearchAgent
from agents.analysis_agent import AnalysisAgent

# Create both agents
research_agent = ResearchAgent()
analysis_agent = AnalysisAgent()

topic = "Latest developments in Generative AI"

# Research phase
print("\n========== RESEARCH PHASE ==========")

research_results = research_agent.research(topic)

# Analysis phase
print("\n========== ANALYSIS PHASE ==========")

analysis_results = analysis_agent.analyze(
    topic,
    research_results
)

# Display final analysis
print("\n========== FINAL RESEARCH ANALYSIS ==========")
print(analysis_results)

print("\n========== PROJECT COMPLETED ==========")