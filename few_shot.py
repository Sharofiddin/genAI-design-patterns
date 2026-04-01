from pydantic_ai import Agent

agent = Agent('groq:llama-3.3-70b-versatile',
              system_prompt="""
              You are an expert on art history. I will describe
a painting. You should identify it.
              """)
result = agent.run_sync(
        """
         Example:
```
Description: shows two small rowboats in the foreground and a red Sun.
Answer:
   Painting: Impression, Sunrise
   Artist: Claude Monet
   Year: 1872
   Significance: Gave the Impressionist movement its name; captured the fleeting 
effects of light and atmosphere, with loose brushstrokes.
```
 
Description: The painting shows a group of people eating at a table under an         outside tent. The men are wearing boating hats.
        """)
print(result.output)
