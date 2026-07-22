from __future__ import annotations

import re

from .models import Announcement, ClassifiedAnnouncement
from .taxonomy import PRODUCT_LABELS, PRODUCT_RULES, UNKNOWN


ROUTINE_PATTERNS = (
    r"证券变动月报表",
    r"翌日披露报表",
    r"董事会会议召开日期",
    r"董事名单与其角色和职能",
)

SUPPORT_PATTERNS = (
    r"核查意见",
    r"法律意见",
    r"独立财务顾问报告",
    r"资产评估报告",
    r"审计报告",
    r"保荐书",
    r"专业意见附表",
    r"内幕信息知情人.*自查",
    r"摊薄即期回报",
)

CLARIFICATION_PATTERNS = (
    r"不构成重大资产重组",
    r"不构成重组上市",
    r"不构成关联交易",
    r"符合.*重大资产重组管理办法",
    r"取消.*配套.*资金.*不构成重大调整",
    r"前十二个月.*购买.*出售资产",
    r"前\s*12\s*个月.*购买.*出售资产",
)


def contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def classify_role(title: str) -> str:
    if contains_any(title, ROUTINE_PATTERNS):
        return "routine"
    if contains_any(title, SUPPORT_PATTERNS):
        return "support"
    if contains_any(title, CLARIFICATION_PATTERNS):
        return "clarification"
    if re.search(r"终止|取消", title):
        return "cancellation"
    if re.search(r"发行情况报告书|发行结果|新增股份上市|挂牌并上市|完成交割|资产过户|实施完毕|项目结项", title):
        return "completion"
    if re.search(r"进展|审核|问询|受理|注册|备案|延期|变更|调整|实施", title):
        return "progress"
    return "primary"


def classify_subject(title: str, text: str = "") -> str:
    evidence = f"{title} {text[:500]}"
    if "实际控制人" in evidence:
        return "actual_controller"
    if "控股股东" in evidence:
        return "controlling_shareholder"
    if re.search(r"持股\s*5%|持股百分之五", evidence):
        return "major_shareholder"
    if "员工持股" in evidence:
        return "employee_plan"
    if "子公司" in evidence or "孙公司" in evidence:
        return "subsidiary"
    return "listed_company"


def classify_product(announcement: Announcement) -> tuple[str, tuple[str, ...], float]:
    title = announcement.title
    evidence = f"{title} {announcement.text[:600]}"
    scored: list[tuple[float, int, str, tuple[str, ...]]] = []

    for rule in PRODUCT_RULES:
        matched = tuple(term for term in rule.include_terms if term in evidence)
        hint_match = announcement.category_hint in rule.category_hints
        if not matched and not hint_match:
            continue
        penalty = 0.2 if any(term in title for term in rule.exclude_terms) else 0.0
        score = (0.55 if hint_match else 0.0) + min(0.4, 0.12 * len(matched)) - penalty
        longest = max((len(term) for term in matched), default=0)
        scored.append((score, longest, rule.key, matched))

    if not scored:
        return UNKNOWN, (), 0.0

    score, _, product, matched = max(scored, key=lambda item: (item[0], item[1]))
    return product, matched, max(0.0, min(0.99, score))


def cancellation_signal(title: str) -> str | None:
    partial_patterns = (
        r"取消.*配套募集资金.*不构成重大调整",
        r"取消.*募集配套资金.*不构成重大调整",
        r"终止部分募投项目",
    )
    if contains_any(title, partial_patterns):
        return None
    if re.search(r"终止(本次|筹划|实施)?.*(发行|上市|重组|交易|项目|基金|计划)", title):
        return "cancelled"
    if re.search(r"(发行|上市|重组|交易|项目|基金|计划).*(终止|取消)", title):
        return "cancelled"
    return None


def classify_state_signal(product: str, title: str, role: str) -> str | None:
    if product == UNKNOWN or role in {"routine", "support", "clarification"}:
        return None

    cancelled = cancellation_signal(title)
    if cancelled:
        return cancelled

    rules: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
        "equity_financing": (
            ("completed", ("发行情况报告书", "发行结果", "新增股份上市")),
            ("issuing", ("发行公告", "申购", "缴款", "发行对象及结果")),
            ("registered", ("同意注册", "注册批复")),
            ("review", ("交易所受理", "申请获得受理", "审核通过", "提交注册", "问询")),
            ("internal_approved", ("股东大会审议通过", "股东大会通过")),
            ("planning", ("发行预案", "向特定对象发行.*预案", "发行方案", "筹划向特定对象发行", "简易程序")),
        ),
        "overseas_listing": (
            ("listed", ("挂牌并上市交易", "正式上市")),
            ("issuing", ("全球发售", "招股章程", "发行价格", "配发结果")),
            ("approved", ("聆讯通过", "上市委员会批准", "原则上批准上市")),
            ("submitted", ("递交境外上市", "递交.*上市申请", "刊发申请资料", "申请获受理")),
            ("filed", ("备案通知书", "完成境外发行上市备案")),
            ("planning", ("筹划发行H股", "拟发行H股", "聘请.*审计机构", "董事会.*发行H股", "发行H股并上市")),
        ),
        "asset_securitization": (
            ("listed", ("基金上市交易", "REITs上市", "挂牌转让")),
            ("issuing", ("发售公告", "询价公告", "认购申请确认比例")),
            ("approved", ("准予注册", "审核通过")),
            ("review", ("申请获受理", "反馈意见", "问询回复")),
            ("planning", ("拟开展资产证券化", "申报REITs", "发行资产支持专项计划")),
        ),
        "convertible_bond": (
            ("redeemed", ("到期兑付", "摘牌", "赎回结果")),
            ("outstanding", ("上市公告书", "转股结果", "付息", "回售")),
            ("issuing", ("发行公告", "申购", "配售")),
            ("registered", ("同意注册", "注册批复")),
            ("review", ("受理", "审核通过", "问询")),
            ("planning", ("发行预案", "发行方案")),
        ),
        "debt_financing": (
            ("redeemed", ("兑付完成", "到期兑付", "摘牌")),
            ("outstanding", ("付息", "跟踪评级", "回售")),
            ("issuing", ("发行公告", "簿记", "发行情况", "发行结果")),
            ("registered", ("获准注册", "接受注册通知书")),
            ("planning", ("拟发行", "发行预案", "注册申请")),
        ),
        "ma_transaction": (
            ("completed", ("完成交割", "资产过户", "标的资产过户", "实施完毕")),
            ("closing", ("交割", "过户进展")),
            ("approved", ("审核通过", "获得核准", "同意注册")),
            ("review", ("审核问询", "问询函回复", "交易所审核", "申请获受理")),
            ("disclosed", ("重组预案", "交易草案", "发行股份购买资产报告书")),
            ("planning", ("筹划重大资产重组", "筹划发行股份购买资产", "停牌筹划")),
        ),
        "capex_project": (
            ("completed", ("项目结项", "竣工投产", "正式投产", "建设完成")),
            ("cancelled", ("终止募投项目", "取消投资项目")),
            ("delayed", ("募投项目延期", "暂缓实施", "建设延期")),
            ("changed", ("变更募集资金用途", "调整募投项目", "变更募投项目")),
            ("building", ("项目进展", "开工建设", "建设进展", "试生产")),
            ("planning", ("投资建设", "签署投资协议", "拟建设", "募投项目可行性")),
        ),
        "industry_fund": (
            ("exited", ("退出投资基金", "基金清算", "转让基金份额")),
            ("operating", ("基金运行", "延长存续", "基金投资")),
            ("established", ("完成备案", "完成工商登记", "基金设立完成")),
            ("planning", ("拟设立", "参与设立", "共同投资基金")),
        ),
        "cash_management": (
            ("matured", ("理财产品到期", "收回现金管理产品", "赎回理财产品")),
            ("invested", ("购买理财产品", "现金管理进展")),
            ("authorized", ("使用闲置自有资金", "使用闲置募集资金", "现金管理额度")),
        ),
        "risk_hedging": (
            ("expired", ("授权到期", "终止套期保值")),
            ("active", ("套期保值进展", "衍生品交易进展")),
            ("authorized", ("拟开展", "年度套期保值", "开展外汇衍生品", "开展期货和衍生品")),
        ),
        "shareholder_service": (
            ("completed", ("减持完成", "增持完成", "回购完成", "解除质押", "协议转让完成")),
            ("active", ("减持进展", "增持进展", "回购进展", "股份质押", "协议转让")),
            ("planned", ("减持计划", "增持计划", "回购股份方案", "限售股份上市流通")),
        ),
        "equity_incentive": (
            ("completed", ("激励计划实施完成", "员工持股计划完成", "终止实施")),
            ("vesting", ("归属条件成就", "解除限售条件成就", "行权")),
            ("granted", ("首次授予", "授予限制性股票", "授予股票期权")),
            ("planning", ("激励计划草案", "员工持股计划草案")),
        ),
    }

    for state, patterns in rules.get(product, ()):
        for pattern in patterns:
            if re.search(pattern, title):
                return state
    return None


def classify_announcement(announcement: Announcement) -> ClassifiedAnnouncement:
    role = classify_role(announcement.title)
    product, matched_terms, confidence = classify_product(announcement)
    state_signal = classify_state_signal(product, announcement.title, role)
    if role in {"routine", "support", "clarification"}:
        confidence = min(confidence, 0.8)
    return ClassifiedAnnouncement(
        announcement=announcement,
        product=product,
        product_label=PRODUCT_LABELS.get(product, "待识别"),
        role=role,
        subject=classify_subject(announcement.title, announcement.text),
        state_signal=state_signal,
        anchor="",
        confidence=round(confidence, 2),
        matched_terms=matched_terms,
    )
