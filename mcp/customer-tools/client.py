import asyncio

from mcp import Client


MCP_URL = "http://localhost:8000/mcp"


async def main() -> None:

    async with Client(MCP_URL) as client:

        print("\n=== AVAILABLE TOOLS ===")

        result = await client.list_tools()

        for tool in result.tools:

            print("\nNAME:")
            print(tool.name)

            print("DESCRIPTION:")
            print(tool.description)

            print("INPUT SCHEMA:")
            print(tool.input_schema)


if __name__ == "__main__":
    asyncio.run(main())