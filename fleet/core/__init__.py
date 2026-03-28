"""Fleet core — domain models, business rules, interfaces.

This layer has NO external dependencies. It defines:
- Domain models (Task, Project, Agent, Approval, etc.)
- Abstract interfaces (implemented by infra/)
- Business rules (task lifecycle, quality validation, routing)
- URL resolution (from config)

Nothing here imports from infra/, templates/, mcp/, or cli/.
"""