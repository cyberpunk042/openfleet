"""Fleet — OpenClaw Fleet operations library.

Clean architecture for fleet agent operations:
- core/    — domain models, business rules, interfaces (no external deps)
- infra/   — Mission Control, IRC, GitHub, config adapters
- templates/ — markdown formatters for PR, comments, memory, IRC
- mcp/     — MCP server exposing fleet tools to agents
- cli/     — command-line entry points

Code standards:
- Files under 500 lines (700 max with justification)
- Type hints on all public functions
- Docstrings on all public classes and functions
- SRP: one responsibility per module
"""

__version__ = "0.1.0"