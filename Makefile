.PHONY: setup provision status dispatch create-task chat monitor agents agents-register \
       mc-up mc-down mc-logs irc-up irc-down irc-connect sync board-setup \
       skills-list skills-install skill-install skills-sync integrate trace \
       gateway gateway-stop gateway-restart refresh-auth logs fleet-setup changelog clean

# ─── Setup & Provision ──────────────────────────────────────────────────────

# Full setup from scratch (clone → running fleet)
setup:
	bash setup.sh

# Re-provision agents (after SOUL.md or config changes)
provision:
	bash scripts/configure-openclaw.sh
	bash scripts/push-soul.sh

# ─── Fleet Operations ───────────────────────────────────────────────────────

# Comprehensive fleet status (agents, tasks, activity)
status:
	@bash scripts/fleet-status.sh

# Create task: make create-task TITLE="..." AGENT=architect PROJECT=nnrt DESC="..." DISPATCH=true
create-task:
	@bash scripts/create-task.sh "$(TITLE)" \
		$(if $(AGENT),--agent $(AGENT)) \
		$(if $(DESC),--desc "$(DESC)") \
		$(if $(PRIORITY),--priority $(PRIORITY)) \
		$(if $(PROJECT),--project $(PROJECT)) \
		$(if $(DISPATCH),--dispatch)

# Integrate agent work into target project: make integrate TASK=<uuid> TARGET=/path/to/project
integrate:
	@bash scripts/integrate-task.sh $(TASK) $(TARGET)

# Dispatch task: make dispatch AGENT=architect TASK=<uuid> [PROJECT=nnrt]
dispatch:
	@bash scripts/dispatch-task.sh $(AGENT) $(TASK) $(if $(PROJECT),--project $(PROJECT))

# Monitor a task in real-time: make monitor TASK=<uuid>
monitor:
	@bash scripts/monitor-task.sh $(TASK)

# Full task trace (details, activity, worktree, commits): make trace TASK=<uuid>
trace:
	@bash scripts/trace-task.sh $(TASK)

# Chat with agents: make chat MSG="your message" or make chat MSG="@architect review this"
chat:
	@bash scripts/chat-agent.sh $(MSG)

# Watch agent events in real-time: make watch [AGENT=architect]
watch:
	@bash scripts/ws-monitor.sh $(if $(AGENT),--agent $(AGENT))

# List all gateway sessions
sessions:
	@bash scripts/ws-monitor.sh --sessions

# ─── Agents ─────────────────────────────────────────────────────────────────

agents:
	@openclaw agents list

agents-register:
	bash scripts/register-agents.sh

# ─── Skills ────────────────────────────────────────────────────────────────

# List skills that would be installed
skills-list:
	@bash scripts/install-skills.sh --list

# Install configured skills on the gateway
skills-install:
	@bash scripts/install-skills.sh

# Install a specific skill: make skill-install SKILL=pdf
skill-install:
	@bash scripts/install-skills.sh --skill $(SKILL)

# Re-sync skill packs from source repos
skills-sync:
	@bash scripts/register-skill-packs.sh

# ─── Infrastructure ─────────────────────────────────────────────────────────

mc-up:
	docker compose up -d
	@echo "Waiting for MC..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if curl -sf http://localhost:8000/health > /dev/null 2>&1; then \
			echo "MC ready: http://localhost:3000"; \
			break; \
		fi; \
		sleep 3; \
	done

mc-down:
	docker compose down

mc-logs:
	docker compose logs -f --tail=50

# IRC
irc-up:
	@bash scripts/setup-irc.sh

irc-down:
	@bash scripts/stop-irc.sh

irc-connect:
	@echo "Open The Lounge in your browser:"
	@echo "  http://localhost:9000"
	@echo "  User: fleet  Pass: fleet"
	@echo ""
	@echo "Or use a CLI client:"
	@echo "  weechat: /server add fleet localhost/6667 && /connect fleet && /join \#fleet,\#alerts,\#reviews"
	@echo "  irssi:   /connect localhost 6667 && /join \#fleet && /join \#alerts && /join \#reviews"

# The Lounge web IRC client
lounge-up:
	@bash scripts/setup-lounge.sh

lounge-down:
	@docker compose stop lounge && echo "The Lounge stopped"

lounge-open:
	@echo "http://localhost:9000  (fleet/fleet)"

gateway:
	@if ss -tlnp 2>/dev/null | grep -q ":18789"; then \
		echo "Gateway already running"; \
	else \
		openclaw gateway run --port 18789 & \
		sleep 5; \
		echo "Gateway started on ws://0.0.0.0:18789"; \
	fi

gateway-stop:
	@pkill -x openclaw-gateway 2>/dev/null && echo "Gateway stopped" || echo "Gateway not running"

# Refresh auth token and restart gateway
refresh-auth:
	@bash scripts/refresh-auth.sh --restart-gateway

gateway-restart: gateway-stop
	@sleep 3
	@openclaw gateway run --port 18789 &
	@sleep 5
	@echo "Gateway restarted"

logs:
	@tail -f /tmp/openclaw/openclaw-$$(date +%Y-%m-%d).log 2>/dev/null || echo "No log file found"

fleet-setup:
	python3 -m gateway.setup

# Sync tasks ↔ PRs (one-shot: merge detection, auto-close, worktree cleanup)
sync:
	@bash scripts/fleet-sync.sh

# Start sync daemon (background, 60s interval)
sync-start:
	@bash scripts/fleet-sync-daemon.sh &
	@echo "Sync daemon started in background"

# Stop sync daemon
sync-stop:
	@if [ -f .sync.pid ]; then kill $$(cat .sync.pid) 2>/dev/null && echo "Sync daemon stopped" || echo "Not running"; rm -f .sync.pid; else echo "Not running"; fi

# Board state monitor (background, 5min interval)
monitor-start:
	@bash scripts/fleet-monitor-daemon.sh &
	@echo "Monitor daemon started"

monitor-stop:
	@if [ -f .monitor.pid ]; then kill $$(cat .monitor.pid) 2>/dev/null && echo "Monitor stopped" || echo "Not running"; rm -f .monitor.pid; else echo "Not running"; fi

# Daily digest
digest:
	@bash scripts/fleet-digest.sh

digest-preview:
	@bash scripts/fleet-digest.sh --dry-run

# Configure board custom fields and tags
board-setup:
	@bash scripts/configure-board.sh

# Generate changelog from conventional commits
changelog:
	@bash scripts/generate-changelog.sh

# ─── Cleanup ────────────────────────────────────────────────────────────────

clean:
	docker compose down -v
	@echo "Docker volumes removed. Config preserved."