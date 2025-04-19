MCP Unpacked: My thoughts on the Model Context Protocol

MCP Model Context Protcol (MCP) is a protocol designed to facilitate the interaction between AI models and external tools or APIs. It allows AI models to call functions, retrieve data, and perform actions in a structured manner. The protocol defines a standard way for AI models to communicate with tools, ensuring compatibility and ease of integration.

MCP follows a client-server architecture, where the client (AI model) sends requests to the server (tool or API) and receives responses. 

The concept of MCP is very similar to the RPC (Remote Procedure Call) paradigm, where a client can invoke methods or functions on a remote server as if they were local. If we borrow the RPC concept and design consideration, MCP requires not only designing the core functionality but also addressing essential concerns like versioning, authentication, error handling, and security.

That's purpose of this article, to discuss the design consideration of MCP, and how it can be used to build a robust and scalable system.

## Version Control in MCP
Versioning in the API and RPC world is fundamental because it guarantees a controlled evolution of your system without breaking existing integrations.

For example, imagine you have built a payment processing API used by several applications. In the initial release (v1), the API's endpoint /api/v1/processPayment accepts a fixed set of parameters—say, the amount, currency, and payment method—and returns a simple confirmation. Over time, business requirements change, and you need to include additional information like discounts, taxes, or promotional codes. Instead of modifying the existing endpoint (which could break all clients that rely on the v1 format), you introduce a new version (v2).

In this scenario, existing clients can continue to call /api/v1/processPayment without disruption, while new clients—or those ready to adopt the new features—can switch to /api/v2/processPayment, which expects the extended set of parameters. By doing so, you control the evolution of your system, ensuring backward compatibility while still allowing innovation and growth.

This versioning strategy also applies to RPC-based systems. A client might include a header or a parameter like X-API-Version: 2.0 with its call, enabling the server to handle the request using the appropriate logic for version 2. This approach ensures that any enhancements or breaking changes are isolated from legacy clients, preserving stability and reducing the risk of integration failures.

In the MCP specification, it defines Version Negociation as per
https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle#version-negotiation

```
In the initialize request, the client MUST send a protocol version it supports. This SHOULD be the latest version supported by the client.

If the server supports the requested protocol version, it MUST respond with the same version. Otherwise, the server MUST respond with another protocol version it supports. This SHOULD be the latest version supported by the server.

If the client does not support the version in the server’s response, it SHOULD disconnect.
```
Take the current SDK as an example, the MCP client sends a request to the server with the version it supports. 

JSONRPCRequest(method='initialize', params={'protocolVersion': '2024-11-05', 'capabilities': {'sampling': {}, 'roots': {'listChanged': True}}, 'clientInfo': {'name': 'mcp', 'version': '0.1.0'}}, jsonrpc='2.0', id=0)

The server then responds with the version it supports. 

JSONRPCResponse(jsonrpc='2.0', id=0, result={'protocolVersion': '2024-11-05', 'capabilities': {'experimental': {}, 'prompts': {'listChanged': False}, 'resources': {'subscribe': False, 'listChanged': False}, 'tools': {'listChanged': False}}, 'serverInfo': {'name': 'weather', 'version': '1.6.0'}})

The client can then use this information to determine which version of the MCP server it is communicating with and adjust its behavior accordingly.

## Authorization in MCP
Authorization is a critical aspect of any API or RPC system, as it ensures that only authorized clients can access specific resources or perform certain actions. In the context of MCP,  MCP client MUST use the Authorization request header field