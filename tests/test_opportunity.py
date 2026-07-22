import unittest
from datetime import date

from ashare_event_engine.linker import link_announcements
from ashare_event_engine.models import FinancialSnapshot
from ashare_event_engine.opportunity import build_opportunity_lead
from ashare_event_engine.state_machine import advance_events
from tests.helpers import classified


class OpportunityTest(unittest.TestCase):
    def test_active_capex_event_with_funding_signal_is_a1(self):
        item = classified("P1", "关于投资建设Alpha高端材料项目的公告", date(2026, 5, 1), "重大项目_扩产")
        event = advance_events(link_announcements([item]))[0]
        snapshot = FinancialSnapshot(
            company_id="900001",
            revenue=100,
            operating_cash_flow=5,
            capex=20,
            cash=5,
            restricted_cash=1,
            short_term_debt=10,
        )
        lead = build_opportunity_lead(event, date(2026, 7, 1), snapshot)
        self.assertEqual(lead.evidence_level, "A1")
        self.assertEqual(lead.lead_status, "active_research_window")

    def test_completed_event_is_closed_and_score_is_capped(self):
        items = [
            classified("E1", "关于2025年度向特定对象发行股票预案的公告", date(2025, 6, 1), "定增_配股"),
            classified("E2", "关于2025年度向特定对象发行股票发行情况报告书", date(2026, 4, 1), "定增_配股"),
        ]
        event = advance_events(link_announcements(items))[0]
        lead = build_opportunity_lead(event, date(2026, 7, 1))
        self.assertEqual(lead.lead_status, "closed_or_historical")
        self.assertLessEqual(lead.priority_score, 20)


if __name__ == "__main__":
    unittest.main()
