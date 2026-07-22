import unittest
from datetime import date

from ashare_event_engine.linker import link_announcements
from tests.helpers import classified


class EventLinkerTest(unittest.TestCase):
    def test_same_equity_plan_is_linked_across_stages(self):
        items = [
            classified("E1", "关于2025年度向特定对象发行股票预案的公告", date(2025, 6, 1), "定增_配股"),
            classified("E2", "关于2025年度向特定对象发行股票获得同意注册批复的公告", date(2026, 1, 1), "定增_配股"),
        ]
        events = link_announcements(items)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0].announcements), 2)

    def test_different_plan_years_are_separate_events(self):
        items = [
            classified("E1", "关于2025年度向特定对象发行股票发行情况报告书", date(2026, 1, 2), "定增_配股"),
            classified("E2", "关于2026年度向特定对象发行股票预案的公告", date(2026, 7, 1), "定增_配股"),
        ]
        events = link_announcements(items)
        self.assertEqual(len(events), 2)

    def test_distinct_capex_projects_are_not_merged(self):
        items = [
            classified("P1", "关于投资建设Alpha高端材料项目的公告", date(2026, 1, 1), "重大项目_扩产"),
            classified("P2", "关于投资建设Beta电子材料项目的公告", date(2026, 2, 1), "重大项目_扩产"),
        ]
        events = link_announcements(items)
        self.assertEqual(len(events), 2)
        self.assertNotEqual(events[0].anchor, events[1].anchor)

    def test_capex_project_progress_is_linked_to_original_project(self):
        items = [
            classified("P1", "关于投资建设Alpha高端材料项目的公告", date(2026, 1, 1), "重大项目_扩产"),
            classified("P2", "关于Alpha高端材料项目建设进展的公告", date(2026, 4, 1), "重大项目_扩产"),
        ]
        events = link_announcements(items)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0].announcements), 2)


if __name__ == "__main__":
    unittest.main()
