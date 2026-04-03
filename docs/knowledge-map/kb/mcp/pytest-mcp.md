# Pytest MCP Server

**Type:** External MCP Server
**Package:** pytest-mcp-server (pip)
**Transport:** command (python -m pytest_mcp_server)
**Tools:** test failures analysis, coverage reports, debug traces
**Installed for:** software-engineer, qa-engineer

## What It Does

Pytest integration via MCP. Analyzes test failures with stack traces, generates coverage reports, provides debug traces for failing tests. Goes beyond just running tests — provides structured analysis of WHY tests fail.

## Fleet Use Case

Engineer runs tests during WORK stage and needs to understand failures. QA validates test coverage and failure patterns during review. pytest-mcp provides structured test intelligence instead of raw pytest output.

## Relationships

- INSTALLED FOR: software-engineer, qa-engineer
- INSTALLED VIA: pip install pytest-mcp-server (setup-mcp-deps.sh)
- CONNECTS TO: feature-test skill (write and run tests)
- CONNECTS TO: fleet-test skill (analyze test results for review)
- CONNECTS TO: quality-coverage skill (coverage reports)
- CONNECTS TO: /debug command (pytest-mcp provides debug traces)
- CONNECTS TO: foundation-testing skill (testing methodology)
