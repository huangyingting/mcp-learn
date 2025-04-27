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

## MCP Tool Selection
The MCP protocol allows the client to select a tool from a list of available tools. The client can specify the tool it wants to use in the request, and the server will execute the corresponding function.

Selecting the right Model Context Protocol (MCP) tools from a wide range of options requires a structured approach. Here's a breakdown of filtering practices to guide your selection: 

1.  **Define Requirements**: Start by clearly defining your specific needs and objectives. Consider the following:

    *   *Data types*: What kinds of data will the MCP tool need to handle (text, images, code, etc.)?
    *   *Model types*: Which models will the MCP tool support (LLMs, diffusion models, etc.)?
    *   *Scalability*: How much data and how many models will the MCP tool need to scale to?
    *   *Integration*: How easily does the MCP tool integrate with your existing infrastructure and workflows?
    *   *Security*: What security and privacy requirements does the MCP tool need to meet?
2.  **Categorize MCP Tools**: Group the available MCP tools into categories based on their primary function. Common categories include:

    *   *Data enrichment*: Tools that add contextual information to data.
    *   *Prompt engineering*: Tools that help design and optimize prompts for language models.
    *   *Model monitoring*: Tools that track model performance and identify issues.
    *   *Bias detection and mitigation*: Tools that identify and mitigate bias in models.
    *   *Explainability*: Tools that provide insights into model decision-making.
3.  **Establish Filtering Criteria**: Define specific criteria for evaluating MCP tools within each category. Examples include:

    *   *Accuracy*: How accurately does the tool perform its intended function?
    *   *Efficiency*: How efficiently does the tool operate in terms of time and resources?
    *   *Cost*: What is the cost of using the tool, including licensing fees and infrastructure costs?
    *   *Ease of use*: How easy is the tool to set up, configure, and use?
    *   *Community support*: How active and helpful is the tool's community?
4.  **Prioritize Criteria**: Assign weights to each filtering criterion based on its importance to your specific needs. For example, if accuracy is paramount, assign it a higher weight than ease of use. This weighted scoring system can help you compare and rank different MCP tools objectively.
5.  **Create a Matrix**: Develop a matrix that lists the MCP tools you're considering along one axis and the filtering criteria along the other axis. Populate the matrix with scores for each tool based on your evaluation. Use the weighted scores to calculate an overall score for each tool.
6.  **Consider Open Source vs. Proprietary**: Evaluate the trade-offs between open-source and proprietary MCP tools. Open-source tools offer greater flexibility and transparency but may require more technical expertise to set up and maintain. Proprietary tools often provide better support and ease of use but may be more expensive and less customizable.
7.  **Evaluate Integration Capabilities**: Assess how well each MCP tool integrates with your existing infrastructure, including data storage, model serving, and monitoring systems. Seamless integration can save time and resources and reduce the risk of compatibility issues.
8.  **Assess Security and Compliance**: Evaluate the security and compliance features of each MCP tool. Ensure that the tool meets your organization's security requirements and complies with relevant regulations, such as GDPR and HIPAA.
9.  **Conduct Proof-of-Concept (POC)**: Before making a final decision, conduct a POC with a small subset of data and models to validate the performance and scalability of the selected MCP tools in your specific environment. This can help you identify any potential issues or limitations before committing to a full-scale deployment.
10. **Iterate and Refine**: Model Context Protocol (MCP) tool selection is an ongoing process. Continuously monitor the performance of the selected tools and iterate on your selection criteria as your needs evolve. Regularly evaluate new MCP tools that emerge in the market to ensure you're using the best possible solutions.