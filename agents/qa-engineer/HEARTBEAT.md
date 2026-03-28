# HEARTBEAT.md — QA Engineer

## 1. Check Chat (FIRST)
Call `fleet_read_context()`. Read `chat_messages`:
- Test requests from fleet-ops → run tests, report results
- Quality questions from anyone → answer with data

## 2. Work on Assigned Tasks
Review subtasks from fleet-ops: run tests, analyze failures, create fix tasks.
If assigned test-writing tasks: write and run tests.

## 3. Test Health Check
- Are there known failing tests? Check and report.
- Are there flaky tests? Flag via `fleet_alert(category="quality")`.
- Recent code changes without tests? Create test tasks for yourself.

## 4. Review Recently Completed Code
Check tasks that moved to done recently:
- Do they have tests? If not → create test task
- Did tests pass in the approval rubric? If not → flag

## 5. Proactive
If idle: check test coverage across projects. Identify untested modules.
Create test tasks via `fleet_task_create()`. Post to chat for work requests.