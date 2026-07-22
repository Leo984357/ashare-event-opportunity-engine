from __future__ import annotations

from dataclasses import dataclass


UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProductRule:
    key: str
    label: str
    category_hints: tuple[str, ...]
    include_terms: tuple[str, ...]
    exclude_terms: tuple[str, ...] = ()


PRODUCT_RULES = (
    ProductRule(
        "equity_financing",
        "定向增发/配股",
        ("定增_配股",),
        ("向特定对象发行", "非公开发行", "配股", "简易程序发行股票"),
        ("发行股份购买资产", "可转换公司债券"),
    ),
    ProductRule(
        "overseas_listing",
        "境外上市/分拆上市",
        ("分拆_H股_REITs",),
        ("发行H股", "H股发行", "境外上市", "分拆上市", "香港联交所", "GDR"),
        ("证券变动月报表", "翌日披露报表"),
    ),
    ProductRule(
        "asset_securitization",
        "资产证券化/REITs",
        ("分拆_H股_REITs",),
        ("REITs", "基础设施公募REIT", "资产证券化", "资产支持专项计划", "ABS"),
    ),
    ProductRule(
        "convertible_bond",
        "可转换公司债券",
        ("可转债",),
        ("可转换公司债券", "可转债", "转债"),
        ("可交换债券",),
    ),
    ProductRule(
        "debt_financing",
        "债务融资工具",
        ("公司债_科创债", "中票_短融_超短融"),
        ("公司债券", "科技创新公司债券", "中期票据", "短期融资券", "超短期融资券", "债务融资工具"),
        ("可转换公司债券",),
    ),
    ProductRule(
        "ma_transaction",
        "并购重组/资产交易",
        ("并购重组",),
        ("重大资产重组", "发行股份购买资产", "收购股权", "出售资产", "控制权变更", "吸收合并"),
        ("不构成重大资产重组",),
    ),
    ProductRule(
        "capex_project",
        "重大项目/扩产",
        ("重大项目_扩产",),
        ("投资建设", "生产基地", "扩产项目", "产能建设", "募投项目", "产业园", "研发中心"),
    ),
    ProductRule(
        "industry_fund",
        "产业基金/CVC",
        ("产业基金",),
        ("产业投资基金", "产业基金", "并购基金", "股权投资基金", "创业投资基金"),
    ),
    ProductRule(
        "cash_management",
        "现金管理",
        ("现金管理",),
        ("闲置自有资金", "闲置募集资金", "现金管理", "委托理财", "结构性存款"),
    ),
    ProductRule(
        "risk_hedging",
        "风险管理/套期保值",
        ("外汇_套保",),
        ("外汇衍生品", "远期结售汇", "套期保值", "商品期货", "衍生品交易"),
    ),
    ProductRule(
        "shareholder_service",
        "股东与股份管理",
        ("回购_增减持_质押",),
        ("减持计划", "增持计划", "股份质押", "解除质押", "股份回购", "协议转让", "限售股份上市流通"),
    ),
    ProductRule(
        "equity_incentive",
        "股权激励/员工持股",
        ("股权激励",),
        ("股权激励", "限制性股票激励", "股票期权激励", "员工持股计划"),
    ),
)


PRODUCT_LABELS = {rule.key: rule.label for rule in PRODUCT_RULES}


STATE_ORDER = {
    "equity_financing": ("planning", "internal_approved", "review", "registered", "issuing", "completed", "cancelled"),
    "overseas_listing": ("planning", "filed", "submitted", "approved", "issuing", "listed", "cancelled"),
    "asset_securitization": ("planning", "review", "approved", "issuing", "listed", "cancelled"),
    "convertible_bond": ("planning", "review", "registered", "issuing", "outstanding", "redeemed", "cancelled"),
    "debt_financing": ("planning", "registered", "issuing", "outstanding", "redeemed", "cancelled"),
    "ma_transaction": ("planning", "disclosed", "review", "approved", "closing", "completed", "cancelled"),
    "capex_project": ("planning", "building", "delayed", "changed", "completed", "cancelled"),
    "industry_fund": ("planning", "established", "operating", "exited", "cancelled"),
    "cash_management": ("authorized", "invested", "matured", "cancelled"),
    "risk_hedging": ("authorized", "active", "expired", "cancelled"),
    "shareholder_service": ("planned", "active", "completed", "cancelled"),
    "equity_incentive": ("planning", "granted", "vesting", "completed", "cancelled"),
}


TERMINAL_STATES = {
    "completed",
    "cancelled",
    "listed",
    "redeemed",
    "exited",
    "matured",
    "expired",
}


ACTIVE_STATES = {
    "planning",
    "internal_approved",
    "review",
    "registered",
    "issuing",
    "filed",
    "submitted",
    "approved",
    "disclosed",
    "closing",
    "building",
    "delayed",
    "changed",
    "established",
    "operating",
    "authorized",
    "invested",
    "active",
    "planned",
    "granted",
    "vesting",
    "outstanding",
}


SERVICE_LINES = {
    "equity_financing": "股权融资与资本市场服务",
    "overseas_listing": "境外上市与跨境资本市场服务",
    "asset_securitization": "资产证券化与REITs服务",
    "convertible_bond": "可转债与债务资本市场服务",
    "debt_financing": "债券与债务融资服务",
    "ma_transaction": "并购重组财务顾问",
    "capex_project": "项目融资与资本开支服务",
    "industry_fund": "产业基金与CVC服务",
    "cash_management": "企业现金管理",
    "risk_hedging": "汇率/商品/利率风险管理",
    "shareholder_service": "股东与股份管理服务",
    "equity_incentive": "股权激励与员工持股服务",
}
