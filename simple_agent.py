from pydantic_ai import Agent

agent = Agent('groq:llama-3.3-70b-versatile',
              system_prompt="You are experienced soccer player")
result = agent.run_sync(
        "How was your day?")
print(result.output)
