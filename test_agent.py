import asyncio

from browser_use import Agent, ChatOllama


async def main():
    llm = ChatOllama(model="qwen3:14b")

    agent = Agent(
        task=(
            "Open https://en.wikipedia.org/wiki/Raptor_Lake. "
            "On this page, locate the Intel Core i7-14700 entry. "
            "Find its total CPU core count. "
            "The answer is a single number. "
            "Do not search the web. "
            "Do not create or modify any files. "
            "Do not perform any other task. "
            "Once you know the number, immediately stop and answer."
        ),
        llm=llm,
    )

    result = await agent.run(max_steps=5)

    print("\nFINAL RESULT:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
