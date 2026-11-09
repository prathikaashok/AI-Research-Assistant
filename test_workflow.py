from workflow.graph import ResearchWorkflow


# Create the workflow
research_workflow = ResearchWorkflow()

# Enter a research topic
topic = "Latest developments in Generative AI"

print("\n===================================")
print(" MULTI-AGENT AI RESEARCH ASSISTANT")
print("===================================")

# Execute the complete workflow
result = research_workflow.run(topic)

print("\n===================================")
print(" WORKFLOW COMPLETED SUCCESSFULLY!")
print("===================================")

print("\nResearch Topic:", result["topic"])

print("\nReport generated successfully!")
print("Check the reports folder for your report.")