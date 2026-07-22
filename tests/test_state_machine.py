import unittest
from datetime import date

from ashare_event_engine.linker import link_announcements
from ashare_event_engine.state_machine import advance_events
from tests.helpers import classified


class StateMachineTest(unittest.TestCase):
    def test_state_is_computed_chronologically(self):
        items = [
            classified("E3", "关于2025年度向特定对象发行股票发行情况报告书", date(2026, 4, 1), "定增_配股"),
            classified("E1", "关于2025年度向特定对象发行股票预案的公告", date(2025, 6, 1), "定增_配股"),
            classified("E2", "关于2025年度向特定对象发行股票获得同意注册批复的公告", date(2026, 1, 1), "定增_配股"),
        ]
        event = advance_events(link_announcements(items))[0]
        self.assertEqual(event.current_state, "completed")
        self.assertEqual([t.to_state for t in event.transitions if t.applied], ["planning", "registered", "completed"])

    def test_clarification_does_not_cancel_ma_event(self):
        items = [
            classified("M1", "关于筹划发行股份购买资产事项的公告", date(2025, 11, 3), "并购重组"),
            classified(
                "M2",
                "关于取消发行股份购买资产配套资金募集暨交易方案不构成重大调整的说明",
                date(2026, 1, 15),
                "并购重组",
            ),
            classified("M3", "关于发行股份购买资产报告书草案的公告", date(2026, 3, 20), "并购重组"),
        ]
        event = advance_events(link_announcements(items))[0]
        self.assertEqual(event.current_state, "disclosed")


if __name__ == "__main__":
    unittest.main()
