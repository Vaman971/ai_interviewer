import asyncio
import logging
from agents.interviewer_agent import InterviewerAgent
logging.basicConfig(level=logging.DEBUG)

async def main():
    agent = InterviewerAgent()
    try:
        res = await agent.call_llm('What is python?', 'You are a friendly interviewer. Evaluate the answer fairly. Always respond with valid JSON.')
        print("SUCCESS:", res)
    except Exception as e:
        print("CAUGHT EXCEPTION IN BASE AGENT?", e)

if __name__ == '__main__':
    asyncio.run(main())
