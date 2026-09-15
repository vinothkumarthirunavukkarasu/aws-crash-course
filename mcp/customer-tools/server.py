from mcp.server.mcpserver import MCPServer


mcp = MCPServer(
    "Project X Customer Tools"
)


CUSTOMERS = {
    "C12345": {
        "customerId": "C12345",
        "name": "John Smith",
        "status": "ACTIVE",
        "address": {
            "street": "100 Old Street",
            "city": "Jacksonville",
            "state": "FL",
            "zip": "32256",
        },
    },
    "C67890": {
        "customerId": "C67890",
        "name": "Mary Jones",
        "status": "ACTIVE",
        "address": {
            "street": "500 Bay Street",
            "city": "Jacksonville",
            "state": "FL",
            "zip": "32202",
        },
    },
}


@mcp.tool()
def get_customer(customer_id: str) -> dict:
    """Retrieve a customer by customer ID."""

    customer = CUSTOMERS.get(customer_id)

    if customer is None:
        return {
            "found": False,
            "customerId": customer_id,
        }

    return {
        "found": True,
        "customer": customer,
    }


@mcp.tool()
def validate_address(
    street: str,
    city: str,
    state: str,
    zip_code: str,
) -> dict:
    """Validate the minimum requirements for a US address."""

    errors = []

    if not street.strip():
        errors.append("street is required")

    if not city.strip():
        errors.append("city is required")

    if len(state.strip()) != 2:
        errors.append("state must be a 2-letter code")

    if len(zip_code.strip()) != 5 or not zip_code.strip().isdigit():
        errors.append("zip code must contain 5 digits")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "normalizedAddress": {
            "street": street.strip(),
            "city": city.strip(),
            "state": state.strip().upper(),
            "zip": zip_code.strip(),
        },
    }


@mcp.tool()
def update_customer_address(
    customer_id: str,
    street: str,
    city: str,
    state: str,
    zip_code: str,
) -> dict:
    """Update the address for an existing customer."""

    customer = CUSTOMERS.get(customer_id)

    if customer is None:
        return {
            "updated": False,
            "reason": "CUSTOMER_NOT_FOUND",
            "customerId": customer_id,
        }

    customer["address"] = {
        "street": street.strip(),
        "city": city.strip(),
        "state": state.strip().upper(),
        "zip": zip_code.strip(),
    }

    return {
        "updated": True,
        "customerId": customer_id,
        "address": customer["address"],
    }


if __name__ == "__main__":
    mcp.run(
        "streamable-http",
        host="0.0.0.0",
        port=8000,
        stateless_http=True,
    )
