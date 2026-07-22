import unittest
from datetime import date

from ashare_event_engine.models import Announcement
from ashare_event_engine.pipeline import run_pipeline


class PipelineAuditTest(unittest.TestCase):
    def test_audit_reports_duplicates_and_abstentions(self):
        known = Announcement("A1", "900001", "示例公司", "关于使用闲置自有资金进行现金管理的公告", date(2026, 1, 1), category_hint="现金管理")
        duplicate = Announcement("A1", "900001", "示例公司", "关于使用闲置自有资金进行现金管理的公告", date(2026, 1, 1), category_hint="现金管理")
        unknown = Announcement("A2", "900002", "示例公司二", "关于召开年度股东大会的通知", date(2026, 1, 2))
        result = run_pipeline([known, duplicate, unknown])
        self.assertEqual(result["audit"]["duplicate_announcement_ids"], 1)
        self.assertEqual(result["audit"]["unknown_product_count"], 1)
        self.assertEqual(result["audit"]["linked_event_count"], 1)


if __name__ == "__main__":
    unittest.main()
