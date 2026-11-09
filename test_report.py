from agents.research_agent import ResearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.fact_checker import FactCheckerAgent
from agents.report_generator import ReportGenerator


def extract_text(content):
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )

    return str(content)


# Research topic
topic = "Latest developments in Generative AI"

# Initialize all four agents
research_agent = ResearchAgent()
analysis_agent = AnalysisAgent()
fact_checker = FactCheckerAgent()
report_generator = ReportGenerator()

# Step 1: Research
research_results = research_agent.research(topic)

# Step 2: Analysis
analysis = analysis_agent.analyze(topic, research_results)
analysis_text = extract_text(analysis)

# Step 3: Fact-checking
fact_check = fact_checker.fact_check(
    topic,
    research_results,
    analysis_text
)
fact_check_text = extract_text(fact_check)

# Step 4: Generate report
report = report_generator.generate_report(
    topic,
    research_results,
    analysis_text,
    fact_check_text
)

print("\nAll four agents completed successfully!")
print("Your research report has been saved in the reports folder.")