# Docker MCP Server

**Type:** External MCP Server
**Package:** @modelcontextprotocol/server-docker
**Transport:** npx (stdio)
**Tools:** 25 (containers, images, networks, volumes, compose)
**Auth:** Docker socket access
**Installed for:** devops, devsecops

## What It Does

Docker management via MCP. List/start/stop/remove containers, build/pull images, manage networks and volumes, inspect running containers, view logs. Requires Docker socket access.

## Fleet Use Case

DevOps manages fleet infrastructure (docker-compose services: PostgreSQL, Redis, Mission Control, LightRAG, The Lounge). DevSecOps audits container security — image vulnerabilities, network exposure, volume permissions.

## Relationships

- INSTALLED FOR: devops, devsecops-expert
- REQUIRES: Docker socket access (/var/run/docker.sock)
- CONNECTS TO: docker-compose.yaml (fleet infrastructure managed via Docker)
- CONNECTS TO: foundation-docker skill (DevOps Docker operations)
- CONNECTS TO: Trivy/Semgrep (security scanning of container images)
- CONNECTS TO: LightRAG container (managed via this MCP)
