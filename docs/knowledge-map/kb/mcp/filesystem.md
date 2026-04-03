# Filesystem MCP Server

**Type:** External MCP Server
**Package:** @modelcontextprotocol/server-filesystem
**Transport:** npx (stdio)
**Tools:** 8 (read, write, move, search, list, mkdir, stat, edit)
**Installed for:** architect, software-engineer, qa-engineer, devops, devsecops, technical-writer, ux-designer, accountability-generator

## What It Does

Provides sandboxed file system access within a specified workspace directory. Tools: read_file, write_file, edit_file, create_directory, list_directory, move_file, search_files, get_file_info. Operations are restricted to the workspace root passed as argument.

## Fleet Use Case

Most agents need to read and write files in their workspace. The filesystem MCP provides a standardized interface that respects workspace boundaries — agents can't accidentally access files outside their assigned directory.

## Relationships

- INSTALLED FOR: 8 of 10 agents (all except fleet-ops and project-manager who don't need file access)
- WORKSPACE: restricted to agent workspace directory ({{WORKSPACE}})
- CONNECTS TO: Claude Code built-in tools (Read, Write, Edit, Glob, Grep — overlapping but MCP provides additional operations)
- CONNECTS TO: safety-net plugin (additional protection layer on file operations)
