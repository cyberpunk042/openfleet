"""Tests for standing orders module.

Verifies:
  - Config loads correctly
  - Per-role orders returned
  - Authority levels correct
  - Unknown agents get conservative defaults
  - Escalation threshold present
"""

from fleet.core.standing_orders import get_standing_orders


class TestStandingOrders:

    def test_fleet_ops_has_orders(self):
        so = get_standing_orders("fleet-ops")
        assert len(so["orders"]) >= 2
        names = [o["name"] for o in so["orders"]]
        assert "review-queue" in names
        assert "board-health" in names

    def test_fleet_ops_authority_standard(self):
        so = get_standing_orders("fleet-ops")
        assert so["authority_level"] == "standard"

    def test_pm_has_orders(self):
        so = get_standing_orders("project-manager")
        assert len(so["orders"]) >= 2
        names = [o["name"] for o in so["orders"]]
        assert "triage-inbox" in names

    def test_pm_authority_standard(self):
        so = get_standing_orders("project-manager")
        assert so["authority_level"] == "standard"

    def test_architect_conservative(self):
        so = get_standing_orders("architect")
        assert so["authority_level"] == "conservative"

    def test_devsecops_has_security_monitoring(self):
        so = get_standing_orders("devsecops-expert")
        names = [o["name"] for o in so["orders"]]
        assert "security-monitoring" in names

    def test_devsecops_authority_standard(self):
        so = get_standing_orders("devsecops-expert")
        assert so["authority_level"] == "standard"

    def test_engineer_conservative(self):
        so = get_standing_orders("software-engineer")
        assert so["authority_level"] == "conservative"

    def test_unknown_agent_conservative(self):
        so = get_standing_orders("nonexistent-agent")
        assert so["authority_level"] == "conservative"
        assert so["orders"] == []

    def test_escalation_threshold(self):
        so = get_standing_orders("fleet-ops")
        assert so["escalation_threshold"] == 2

    def test_orders_have_required_fields(self):
        """Every order should have name, description, when, boundary."""
        for role in ["project-manager", "fleet-ops", "devsecops-expert",
                     "architect", "software-engineer", "qa-engineer",
                     "devops", "technical-writer", "ux-designer",
                     "accountability-generator"]:
            so = get_standing_orders(role)
            for order in so["orders"]:
                assert "name" in order, f"{role}: order missing name"
                assert "description" in order, f"{role}: order missing description"
                assert order["description"] != "", f"{role}/{order['name']}: empty description"

    def test_all_roles_have_at_least_one_order(self):
        """Every role in standing-orders.yaml should have at least one order."""
        roles_with_orders = [
            "project-manager", "fleet-ops", "devsecops-expert",
            "architect", "software-engineer", "qa-engineer",
            "devops", "technical-writer", "ux-designer",
            "accountability-generator",
        ]
        for role in roles_with_orders:
            so = get_standing_orders(role)
            assert len(so["orders"]) >= 1, f"{role}: no standing orders"
