from typing import List, Optional, Dict
from agno.agent import Agent
from agents.workspace_agent import get_model, db, knowledge

def get_planner_agent(provider, api_key):
    return Agent(
        name="Planner",
        role="Planner",
        model=get_model(provider, api_key),
        description="You are a strategic planner. Your job is to break down complex requests into logical steps.",
        instructions=[
            "1. Analyze the user request.",
            "2. Create a step-by-step execution plan.",
            "3. Decide if you need research (Researcher) or code (Coder).",
            "4. Output the plan clearly.",
        ],
        db=db,
        markdown=True,
    )

def get_researcher_agent(provider, api_key):
    return Agent(
        name="Researcher",
        role="Researcher",
        model=get_model(provider, api_key),
        description="You are an expert researcher. You gather information and analyze data from the knowledge base.",
        instructions=[
            "1. Use the knowledge base to find relevant information.",
            "2. Provide concise notes and evidence.",
            "3. Reference specific parts of the uploaded documents.",
        ],
        db=db,
        knowledge=knowledge,
        search_knowledge=True,
        markdown=True,
    )

def get_coder_agent(provider, api_key):
    return Agent(
        name="Coder",
        role="Coder",
        model=get_model(provider, api_key),
        description="You are an expert software engineer. You write clean, efficient, and well-documented code.",
        instructions=[
            "1. Write code, configuration, or commands based on the plan and research notes.",
            "2. Explain your implementation briefly.",
            "3. Ensure the code is production-ready.",
        ],
        db=db,
        markdown=True,
    )

class MultiAgentOrchestrator:
    def __init__(self, provider, api_key):
        self.planner = get_planner_agent(provider, api_key)
        self.researcher = get_researcher_agent(provider, api_key)
        self.coder = get_coder_agent(provider, api_key)

    def run_cycle(self, user_input: str):
        """
        Runs a Multi-Agent cycle: Planner -> Researcher -> Coder -> Final Review.
        Yields agent messages for streaming.
        """
        # 1. Planner Phase
        yield {"role": "Planner", "content": "Thinking about the plan..."}
        plan_response = self.planner.run(user_input)
        plan_text = plan_response.content
        yield {"role": "Planner", "content": plan_text}

        # 2. Researcher Phase (Conditional - simplified for now)
        yield {"role": "Researcher", "content": "Gathering information..."}
        research_response = self.researcher.run(f"Research requirements for this plan: {plan_text}")
        research_text = research_response.content
        yield {"role": "Researcher", "content": research_text}

        # 3. Coder Phase
        yield {"role": "Coder", "content": "Writing code..."}
        coder_input = f"Plan: {plan_text}\nResearch Notes: {research_text}\nUser Request: {user_input}"
        coder_response = self.coder.run(coder_input)
        coder_text = coder_response.content
        yield {"role": "Coder", "content": coder_text}

        # 4. Final Review
        yield {"role": "Planner", "content": "Finalizing the response..."}
        final_input = f"Review the following work and provide a final answer to the user.\nUser Request: {user_input}\nCoder output: {coder_text}"
        final_response = self.planner.run(final_input)
        yield {"role": "Final Answer", "content": final_response.content}
