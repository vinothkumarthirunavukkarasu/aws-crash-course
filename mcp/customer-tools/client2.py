import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_URL = "http://localhost:8000/mcp"


async def main() -> None:

    async with streamable_http_client(
        MCP_URL,
        terminate_on_close=False,
    ) as (read_stream, write_stream):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            print("\n=== AVAILABLE TOOLS ===")

            tools = await session.list_tools()

            for tool in tools.tools:
                print(f"- {tool.name}")

            print("\n=== GET CUSTOMER ===")

            result = await session.call_tool(
                "get_customer",
                {
                    "customer_id": "C12345"
                },
            )

            print(result)

            print("\n=== VALIDATE ADDRESS ===")

            result = await session.call_tool(
                "validate_address",
                {
                    "street": "123 Main Street",
                    "city": "Jacksonville",
                    "state": "FL",
                    "zip_code": "32256",
                },
            )

            print(result)


if __name__ == "__main__":
    asyncio.run(main())
