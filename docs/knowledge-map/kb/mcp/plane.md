# Plane MCP Server

**Type:** External MCP Server
**Package:** makeplane/plane-mcp-server
**Transport:** npx (stdio)
**Tools:** issues, cycles, modules, projects
**Auth:** Plane API key
**Installed for:** project-manager

## What It Does

Official Plane project management MCP server. Manage issues (create, update, list, assign), cycles (sprints), and modules. Provides standardized MCP interface to Plane instead of direct HTTP API calls.

## Fleet Use Case

PM manages Plane issues which map to fleet tasks. The two-level task model:
- ONE Plane issue → PM task on OCMC → potentially THOUSANDS of OCMC subtasks

Plane MCP provides cleaner integration than the current fleet_plane_* tools which use direct HTTP calls. Both approaches can coexist — fleet_plane_* for fleet-specific operations, Plane MCP for standard Plane operations.

## Relationships

- INSTALLED FOR: project-manager
- AUTH: requires PLANE_API_KEY environment variable
- CONNECTS TO: fleet_plane_* tools (fleet's current Plane integration — direct HTTP)
- CONNECTS TO: fleet-plane skill (PM's Plane sprint management workflow)
- CONNECTS TO: fleet_task_create (Plane issue → OCMC tasks)
- CONNECTS TO: two-level task model (Plane = outer, OCMC = inner)
- CONNECTS TO: DSPD project (devops-solution-product-development hosts Plane)
