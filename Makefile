FLEET = .venv/bin/python -m fleet

.PHONY: setup provision setup-tools validate-agents test clean \
       status create-task dispatch monitor trace chat watch sessions \
       sync sync-start sync-stop daemons-start daemons-stop \
       monitor-start monitor-stop digest quality board-setup \
       agents agents-register skills-list skills-install skills-sync \
       mc-up mc-down mc-logs irc-up irc-down irc-connect lounge-up lounge-down \
       gateway gateway-stop gateway-restart refresh-auth logs changelog integrate \
       codex-setup install-statusline

# ─── Setup & Provision ──────────────────────────────────────────────────────

setup:
	bash setup.sh

provision:
	bash scripts/configure-openclaw.sh
	bash scripts/push-soul.sh

setup-tools:
	bash scripts/setup-agent-tools.sh

validate-agents:
	bash scripts/validate-agents.sh

# ─── Fleet Operations ───────────────────────────────────────────────────────

status:
	@$(FLEET) status

create-task:
	@$(FLEET) create "$(TITLE)" \
		$(if $(AGENT),--agent $(AGENT)) \
		$(if $(DESC),--desc "$(DESC)") \
		$(if $(PRIORITY),--priority $(PRIORITY)) \
		$(if $(PROJECT),--project $(PROJECT)) \
		$(if $(DISPATCH),--dispatch)

dispatch:
	@$(FLEET) dispatch $(AGENT) $(TASK) $(if $(PROJECT),--project $(PROJECT))

trace:
	@$(FLEET) trace $(TASK)

monitor:
	@bash scripts/monitor-task.sh $(TASK)

chat:
	@bash scripts/chat-agent.sh $(MSG)

watch:
	@bash scripts/ws-monitor.sh $(if $(AGENT),--agent $(AGENT))

sessions:
	@bash scripts/ws-monitor.sh --sessions

integrate:
	@bash scripts/integrate-task.sh $(TASK) $(TARGET)

# ─── Sync & Daemons ─────────────────────────────────────────────────────────

sync:
	@$(FLEET) sync

sync-start:
	@$(FLEET) daemon sync --interval 60 &

sync-stop:
	@if [ -f .sync.pid ]; then kill $$(cat .sync.pid) 2>/dev/null && rm -f .sync.pid && echo "Stopped"; else echo "Not running"; fi

daemons-start:
	@$(FLEET) daemon all &

daemons-stop: sync-stop monitor-stop

monitor-start:
	@$(FLEET) daemon monitor --interval 300 &

monitor-stop:
	@if [ -f .monitor.pid ]; then kill $$(cat .monitor.pid) 2>/dev/null && rm -f .monitor.pid && echo "Stopped"; else echo "Not running"; fi

# ─── Reports ────────────────────────────────────────────────────────────────

digest:
	@$(FLEET) digest

digest-preview:
	@$(FLEET) digest --dry-run

quality:
	@$(FLEET) quality

board-setup:
	@bash scripts/configure-board.sh

board:
	@$(FLEET) board $(ACTION)

changelog:
	@bash scripts/generate-changelog.sh

# ─── Auth ────────────────────────────────────────────────────────────────────

refresh-auth:
	@$(FLEET) auth refresh

auth-status:
	@$(FLEET) auth status

# ─── Cache ───────────────────────────────────────────────────────────────────

cache:
	@$(FLEET) cache $(ACTION)

# ─── Agents & Skills ─────────────────────────────────────────────────────────

agents:
	@openclaw agents list

agents-register:
	bash scripts/register-agents.sh

agents-push:
	bash scripts/push-agent-framework.sh

agents-config:
	bash scripts/configure-agent-settings.sh

skills-list:
	@bash scripts/install-skills.sh --list

skills-install:
	@bash scripts/install-skills.sh

skills-sync:
	@bash scripts/register-skill-packs.sh

# ─── Infrastructure ─────────────────────────────────────────────────────────

mc-up:
	docker compose up -d
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		curl -sf http://localhost:8000/health > /dev/null 2>&1 && echo "MC ready" && break; sleep 3; done

mc-down:
	docker compose down

mc-logs:
	docker compose logs -f --tail=50

irc-up:
	@bash scripts/setup-irc.sh

irc-down:
	@bash scripts/stop-irc.sh

irc-connect:
	@echo "The Lounge: http://localhost:9000 (fleet/fleet)"

lounge-up:
	@bash scripts/setup-lounge.sh

lounge-down:
	@docker compose stop lounge

gateway:
	@ss -tlnp 2>/dev/null | grep -q ":18789" && echo "Already running" || \
		(openclaw gateway run --port 18789 & sleep 5 && echo "Started")

gateway-stop:
	@pkill -x openclaw-gateway 2>/dev/null && echo "Stopped" || echo "Not running"

gateway-restart: gateway-stop
	@sleep 3 && openclaw gateway run --port 18789 & sleep 5 && echo "Restarted"

logs:
	@tail -f /tmp/openclaw/openclaw-$$(date +%Y-%m-%d).log 2>/dev/null || echo "No log"

fleet-setup:
	python3 -m gateway.setup

codex-setup:
	bash scripts/install-codex-plugin.sh

install-statusline:
	bash scripts/install-statusline.sh

# ─── Testing & Cleanup ──────────────────────────────────────────────────────

test:
	@$(FLEET:python=pytest) fleet/tests/ -v --tb=short 2>/dev/null || .venv/bin/python -m pytest fleet/tests/ -v --tb=short

clean:
	docker compose down -v
	@echo "Docker volumes removed."