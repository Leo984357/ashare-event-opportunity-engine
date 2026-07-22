import unittest
from datetime import date

from tests.helpers import classified


class ClassifierTest(unittest.TestCase):
    def test_h_share_planning_is_not_submission(self):
        item = classified(
            "H1",
            "关于筹划发行H股股票并在香港联交所上市的公告",
            date(2026, 1, 5),
            "分拆_H股_REITs",
        )
        self.assertEqual(item.product, "overseas_listing")
        self.assertEqual(item.state_signal, "planning")

    def test_h_share_auditor_appointment_is_preparation(self):
        item = classified(
            "H2",
            "关于聘请H股发行及上市审计机构的公告",
            date(2026, 2, 10),
            "分拆_H股_REITs",
        )
        self.assertEqual(item.state_signal, "planning")

    def test_h_share_submission_requires_submission_evidence(self):
        item = classified(
            "H3",
            "关于向香港联交所递交境外上市外资股（H股）发行并上市申请并刊发申请资料的公告",
            date(2026, 5, 8),
            "分拆_H股_REITs",
        )
        self.assertEqual(item.state_signal, "submitted")

    def test_partial_financing_cancellation_is_clarification(self):
        item = classified(
            "M1",
            "关于取消发行股份购买资产配套资金募集暨交易方案不构成重大调整的说明",
            date(2026, 1, 15),
            "并购重组",
        )
        self.assertEqual(item.role, "clarification")
        self.assertIsNone(item.state_signal)

    def test_routine_h_share_monthly_report_is_not_substantive(self):
        item = classified(
            "H4",
            "H股公告-证券变动月报表",
            date(2026, 6, 1),
            "分拆_H股_REITs",
        )
        self.assertEqual(item.role, "routine")
        self.assertIsNone(item.state_signal)


if __name__ == "__main__":
    unittest.main()
