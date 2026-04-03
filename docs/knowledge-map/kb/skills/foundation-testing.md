# foundation-testing

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/foundation-testing/SKILL.md
**Invocation:** /foundation-testing
**Effort:** medium
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Set up comprehensive testing infrastructure: test framework, directory structure mirroring source, fixtures for common setup, mocking utilities, coverage reporting with 80% minimum threshold, test helpers (factories, assertion helpers, API test client), initial smoke tests, and Makefile targets.

## Process

1. Install test framework (pytest/jest/cargo test/go test)
2. Configure:
   - Test runner with sensible defaults
   - Test directory structure mirroring source
   - Fixtures for common setup (database, auth, HTTP client)
   - Mocking utilities
   - Coverage reporting (80% minimum threshold)
   - Test database or in-memory alternatives
3. Create test helpers:
   - Factory functions for test data
   - Assertion helpers for common patterns
   - Test client for API testing
4. Write initial smoke tests verifying project runs
5. Add Makefile targets: `test`, `test-coverage`, `test-watch`
6. Configure CI to run tests

## Rules

- Tests must be FAST (mock external services)
- Every module gets a corresponding test file
- Coverage threshold: 80% minimum
- Tests must be INDEPENDENT (no order dependency)

## Assigned Roles

| Role | Priority | Why |
|------|----------|-----|
| QA | ESSENTIAL | Test infrastructure is QA's domain |
| Engineer | ESSENTIAL | Engineers need test infrastructure to write tests |
| DevOps | RECOMMENDED | CI integration for test execution |

## Methodology Stages

| Stage | Usage |
|-------|-------|
| work | Set up test infrastructure in new or existing project |

## Relationships

- DEPENDS ON: foundation-deps (test framework must be installed as dependency)
- FOLLOWED BY: feature-test (write tests using the infrastructure this sets up)
- CONNECTS TO: quality-coverage skill (verify coverage meets 80% threshold)
- CONNECTS TO: fleet_task_complete (tests run as quality gate before PR creation)
- CONNECTS TO: pytest-mcp server (deep pytest integration — failures, coverage, debug trace)
- CONNECTS TO: test-driven-development skill (Superpowers — TDD uses this test infrastructure)
- CONNECTS TO: foundation-ci skill (CI pipeline runs these tests)
- CONNECTS TO: challenge_automated.py (automated challenges run tests as pattern checks)
- CONNECTS TO: fleet-test skill (fleet QA runs and analyzes test results during review)
- OUR FLEET: 1732+ tests using pytest, mirroring fleet/ structure in fleet/tests/
