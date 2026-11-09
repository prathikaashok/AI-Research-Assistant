from agents.research_agent import ResearchAgent

# Create Research Agent
research_agent = ResearchAgent()

# Choose a research topic
topic = "Latest developments in Generative AI"

# Perform research
results = research_agent.research(topic)

# Display results
print("\n========== RESEARCH REPORT ==========")

for index, result in enumerate(results, start=1):
    print(f"\nResult {index}")
    print("Title:", result["title"])
    print("URL:", result["url"])
    print("Content:", result["content"])

print("\n========== RESEARCH COMPLETED ==========")