from typing import TypedDict, List

from langgraph.graph import StateGraph, START, END

from agents.research_agent import ResearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.fact_checker import FactCheckerAgent
from agents.report_generator import ReportGenerator


# Define the workflow state
class ResearchState(TypedDict):
    topic: str
    research_data: List[dict]
    analysis: str
    fact_check: str
    report: str


# Convert Gemini response into readable text
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


class ResearchWorkflow:

    def __init__(self):

        # Initialize all agents
        self.research_agent = ResearchAgent()
        self.analysis_agent = AnalysisAgent()
        self.fact_checker = FactCheckerAgent()
        self.report_generator = ReportGenerator()

        # Build the LangGraph workflow
        self.workflow = self.build_workflow()

    def research_node(self, state: ResearchState):

        print("\n--- Research Node ---")

        research_data = self.research_agent.research(
            state["topic"]
        )

        return {"research_data": research_data}

    def analysis_node(self, state: ResearchState):

        print("\n--- Analysis Node ---")

        analysis = self.analysis_agent.analyze(
            state["topic"],
            state["research_data"]
        )

        return {"analysis": extract_text(analysis)}

    def fact_check_node(self, state: ResearchState):

        print("\n--- Fact-Checking Node ---")

        fact_check = self.fact_checker.fact_check(
            state["topic"],
            state["research_data"],
            state["analysis"]
        )

        return {"fact_check": extract_text(fact_check)}

    def report_node(self, state: ResearchState):

        print("\n--- Report Generation Node ---")

        report = self.report_generator.generate_report(
            state["topic"],
            state["research_data"],
            state["analysis"],
            state["fact_check"]
        )

        return {"report": report}

    def build_workflow(self):

        graph = StateGraph(ResearchState)

        # Add agents as workflow nodes
        graph.add_node("research", self.research_node)
        graph.add_node("analysis", self.analysis_node)
        graph.add_node("fact_check", self.fact_check_node)
        graph.add_node("report", self.report_node)

        # Define execution order
        graph.add_edge(START, "research")
        graph.add_edge("research", "analysis")
        graph.add_edge("analysis", "fact_check")
        graph.add_edge("fact_check", "report")
        graph.add_edge("report", END)

        return graph.compile()

    def run(self, topic: str):

        initial_state = {
            "topic": topic,
            "research_data": [],
            "analysis": "",
            "fact_check": "",
            "report": ""
        }

        return self.workflow.invoke(initial_state)