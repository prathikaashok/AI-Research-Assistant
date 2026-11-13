# Multi-Agent AI Research Assistant



An AI-powered research application that automates information gathering, analysis, fact-checking, and research report generation using multiple specialized AI agents.



Built with Python, Streamlit, LangGraph, Tavily, and Google Gemini.



\## 🚀 Project Overview



Researching a topic often requires searching multiple sources, analysing information, verifying claims, and preparing a structured report.



This project addresses that workflow using a multi-agent architecture. Each agent performs a specialized task, and LangGraph coordinates the overall process.



The application provides:



\- Automated web research.

\- AI-powered relevance evaluation.

\- Research analysis and summarization.

\- Fact-checking of generated findings.

\- Structured Markdown report generation.

\- Downloadable research reports.

\- Offline demo mode using a previously generated report.



\## 🏗️ System Architecture



The application follows this workflow:



```text

&#x20;            User Input

&#x20;                 |

&#x20;                 v

&#x20;            Research Agent

&#x20;                 |

&#x20;         Tavily Web Search

&#x20;                 |

&#x20;                 v

&#x20;            Analysis Agent

&#x20;                 |

&#x20;                 v

&#x20;           Fact Checker Agent

&#x20;                 |

&#x20;                 v

&#x20;            Report Generator

&#x20;                 |

&#x20;                 v

&#x20;         Structured Research Report

&#x20;                 |

&#x20;                 v

&#x20;            Streamlit UI

```



\### AI Agents



\*\*1. Research Agent\*\*

\- Searches the web using Tavily.

\- Collects relevant information from multiple sources.

\- Evaluates source relevance and credibility.

\- Filters duplicate and unsuitable results.



\*\*2. Analysis Agent\*\*

\- Analyses collected research information.

\- Identifies important findings.

\- Generates structured summaries.



\*\*3. Fact Checker Agent\*\*

\- Reviews generated findings.

\- Evaluates factual consistency against available research.

\- Identifies claims that require caution or verification.



\*\*4. Report Generator\*\*

\- Organizes research findings.

\- Produces a structured Markdown report.

\- Prepares the final output for download.



\### Workflow Orchestration



LangGraph coordinates the agents and manages the research workflow.



\## 🛠️ Technologies Used



| Technology | Purpose |

|---|---|

| Python | Core programming language |

| Streamlit | User interface |

| LangGraph | Multi-agent workflow orchestration |

| LangChain | LLM integration |

| Google Gemini | AI-powered analysis and reasoning |

| Tavily | Web search and information retrieval |

| Markdown | Research report generation |

| python-dotenv | Environment variable management |



\## 📂 Project Structure



```text

AI-Research-Assistant/

│

├── agents/

│   ├── research\_agent.py

│   ├── analysis\_agent.py

│   ├── fact\_checker.py

│   └── report\_generator.py

│

├── workflow/

│   └── graph.py

│

├── reports/

│   ├── Latest\_developments\_in\_Generative\_AI\_report.md

│   └── latest\_development\_in\_generative\_AI\_report.md

│

├── app.py

├── requirements.txt

├── README.md

└── .gitignore

```



\## ⚙️ Installation and Setup



\### 1. Clone the repository



```bash

git clone YOUR\_GITHUB\_REPOSITORY\_URL

```



```bash

cd AI-Research-Assistant

```



\### 2. Create a virtual environment



```bash

python -m venv venv

```



\### 3. Activate the virtual environment



Windows PowerShell:



```powershell

.\\venv\\Scripts\\Activate.ps1

```



\### 4. Install dependencies



```bash

pip install -r requirements.txt

```



\### 5. Configure API keys



Create a `.env` file in the project root directory.



Add your API keys:



```env

GOOGLE\_API\_KEY=your\_google\_api\_key

TAVILY\_API\_KEY=your\_tavily\_api\_key

```



Never upload your `.env` file or expose API keys publicly.



\### 6. Run the application



```bash

streamlit run app.py

```



Open the local URL displayed in your terminal.



\## 🖥️ Application Modes



\### Demo Mode



\- Loads a previously generated research report.

\- Does not require API calls.

\- Allows users to view and download the sample report.

\- Useful for demonstrations when external APIs are unavailable.



\### Live Research Mode



\- Accepts a new research topic.

\- Uses Tavily to retrieve web information.

\- Executes the multi-agent workflow.

\- Generates analysis and fact-checking results.

\- Produces a downloadable research report.



Live mode requires valid API credentials and available external services.



\## 📄 Sample Research Topic



```text

Latest developments in Generative AI

```



The generated report contains research findings and source information.



\## 🔮 Future Improvements



\- Add source citation verification.

\- Improve research evaluation and scoring.

\- Introduce additional specialized agents.

\- Add persistent research history.

\- Improve report formatting and export options.

\- Integrate more research and data sources.



\## 👩‍💻 Author



Developed as a personal Generative AI project to explore multi-agent systems, LLM integration, research automation, and workflow orchestration.


