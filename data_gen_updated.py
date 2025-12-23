                      
"""
使用 excel_parser_service 的表头格式生成订单与库存数据。

功能：
1. 按可配置比例生成线上预订、线下零售订单（移除分销商；线上预订与线下零售的销售员统一随机分配）。
2. 可配置销售员占比，用于分配线上/线下订单的销售员。
3. 生成符合 RequiredHeaders 的订单 Excel，同时输出订单与库存的 SQL 插入语句。
4. 约束：
   - 线下零售客户单个订单的产品种类数量 ≤ 7，单品数量 ≤ 3。
   - 线下零售订单不包含运单号与订单最晚发货日期；下单时间与付款时间相同；订单状态仅为“完成”或退货相关状态。

依赖：pip install -r python/requirements.txt
"""

import argparse
import datetime as dt
import hashlib
import json
import random
import string
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ORDER_HEADERS = [
    "客户类型",
    "会员名",
    "销售员",
    "订单号",
    "运单号",
    "订单状态",
    "下单时间",
    "付款时间",
    "订单最晚发货日期",
    "购买产品",
    "购买数量",
    "退货处理号",
]

INVENTORY_HEADERS = [
    "产品类型",
    "品牌",
    "产品名称",
    "产品型号",
    "产品ID",
    "库存数量",
    "已售数量",
    "状态",
    "预计补货时间",
]

CUSTOMER_TYPE_TO_INT = {
    "线上预定": 0,
    "线下零售": 1,
}

ORDER_STATUS_TO_INT = {
    "新建": 0,
    "待付款": 1,
    "待发货": 2,
    "打包中": 3,
    "待收货": 4,
    "完成": 5,
    "暂停": 6,
    "取消": 7,
    "退货申请中": 8,
    "退货中": 9,
    "未知": 10,
}

INVENTORY_NORMAL_STATUS = 3
ORDER_ID_RANDOM_MIN = 10_000
ORDER_ID_RANDOM_MAX = 99_999
TRACKING_RANDOM_MIN = 1_000_000_000
TRACKING_RANDOM_MAX = 9_999_999_999
EXPECTED_ARRIVAL_PROBABILITY = 0.5
TRACKING_PREFIX = "SF"
UNPAID_PROBABILITY = 0.1
PAYMENT_DELAY_MINUTES = (15, 240)
INVENTORY_STATUS_LABEL_NORMAL = "正常"
ORDER_PREFIX_MAP = {"online": "ONL", "offline": "OFF"}
CUSTOMER_TYPE_LABELS = {"online": "线上预定", "offline": "线下零售"}
EXPECTED_ARRIVAL_DAYS_RANGE = (2, 7)                                              
ORDER_TIME_DAYS_RANGE = (0, 25)                                           
ORDER_TIME_HOURS_RANGE = (0, 10)                                                  
SHIP_DEADLINE_DAYS_RANGE = (2, 5)                                                       
INVENTORY_BUFFER_MIN = 30                                                   
ONLINE_PRODUCT_RANGE = (1, 5)
ONLINE_QUANTITY_RANGE = (1, 5)
OFFLINE_PRODUCT_MAX = 7
OFFLINE_QUANTITY_RANGE = (1, 3)

DEFAULT_SALES_WEIGHTS: Dict[str, float] = {
    "张三": 0.25,
    "李四": 0.2,
    "王五": 0.2,
    "赵六": 0.2,
    "陈七": 0.15,
}



                        
                         
DEFAULT_ONLINE_STATUS_WEIGHTS: Dict[str, float] = {
    "新建": 0.05,
    "待付款": 0.10,
    "待发货": 0.10,
    "打包中": 0.08,
    "待收货": 0.12,
    "完成": 0.5,
    "取消": 0.01,
    "退货申请中": 0.02,
    "退货驳回": 0.01,
    "退货中": 0.01,
}

DEFAULT_OFFLINE_STATUS_WEIGHTS: Dict[str, float] = {
    "完成": 1,
}
PRODUCT_BLUEPRINTS: Sequence[Dict[str, str]] = [
    {"product_type": "粉底液", "manufacturer": "植村秀", "product_name": "持色小方瓶", "product_model": "584"},
    {"product_type": "粉底液", "manufacturer": "植村秀", "product_name": "持色小方瓶", "product_model": "674"},
    {"product_type": "粉底液", "manufacturer": "植村秀", "product_name": "持色小方瓶", "product_model": "774"},
    {"product_type": "眉笔", "manufacturer": "植村秀", "product_name": "砍刀眉笔", "product_model": "05"},
    {"product_type": "眉笔", "manufacturer": "植村秀", "product_name": "砍刀眉笔", "product_model": "02"},
    {"product_type": "口红", "manufacturer": "圣罗兰", "product_name": "小金条", "product_model": "1936"},
    {"product_type": "口红", "manufacturer": "圣罗兰", "product_name": "小金条", "product_model": "314"},
    {"product_type": "口红", "manufacturer": "圣罗兰", "product_name": "小金条", "product_model": "28"},
    {"product_type": "口红", "manufacturer": "圣罗兰", "product_name": "小金条", "product_model": "23"},
    {"product_type": "口红", "manufacturer": "圣罗兰", "product_name": "小金条", "product_model": "1988"},
    {"product_type": "蜜粉饼", "manufacturer": "NARS", "product_name": "定妆大白饼", "product_model": "经典大白饼"},
    {"product_type": "腮红", "manufacturer": "毛戈平", "product_name": "腮红", "product_model": "806"},
    {"product_type": "腮红", "manufacturer": "毛戈平", "product_name": "腮红", "product_model": "802"},
    {"product_type": "腮红", "manufacturer": "毛戈平", "product_name": "腮红", "product_model": "818"},
    {"product_type": "腮红", "manufacturer": "毛戈平", "product_name": "腮红", "product_model": "801"},
    {"product_type": "香水", "manufacturer": "马吉拉", "product_name": "香水", "product_model": "温暖壁炉"},
    {"product_type": "香水", "manufacturer": "马吉拉", "product_name": "香水", "product_model": "田园拾趣"},
    {"product_type": "香水", "manufacturer": "马吉拉", "product_name": "香水", "product_model": "慵懒周末"},
    {"product_type": "香水", "manufacturer": "马吉拉", "product_name": "香水", "product_model": "无尽夏日"},
    {"product_type": "香水", "manufacturer": "马吉拉", "product_name": "香水", "product_model": "春日公园"},
    {"product_type": "口红", "manufacturer": "MAC", "product_name": "子弹头", "product_model": "544"},
    {"product_type": "口红", "manufacturer": "MAC", "product_name": "子弹头", "product_model": "543"},
    {"product_type": "口红", "manufacturer": "MAC", "product_name": "子弹头", "product_model": "549"},
    {"product_type": "口红", "manufacturer": "MAC", "product_name": "子弹头", "product_model": "567"},

]

def gen_member_ids(prefix, count, seed=42):
    rng = random.Random(seed)
    ids = set()
    while len(ids) < count:
        suffix = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(4))
        ids.add(f"{prefix}_{suffix}")
    return list(ids)

CUSTOMER_POOLS = {
    "online": gen_member_ids("MBR", 30, seed=1),
    "offline": gen_member_ids("MBR", 10, seed=2),
}



def _require_workbook():
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError("未安装 openpyxl，请先执行：pip install -r python/requirements.txt") from exc
    return Workbook


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(v, 0.0) for v in weights.values())
    if total <= 0:
        raise ValueError("权重之和必须大于 0")
    return {k: max(v, 0.0) / total for k, v in weights.items()}


def weighted_choice(rng: random.Random, weights: Dict[str, float]) -> str:
    items: List[Tuple[str, float]] = list(weights.items())
    cumulative = 0.0
    pick = rng.random()
    for key, weight in items:
        cumulative += weight
        if pick <= cumulative:
            return key
    return items[-1][0]


def escape_sql(value: str) -> str:
    return value.replace("'", "''")


@dataclass
class InventoryItem:
    product_type: str
    manufacturer: str
    product_name: str
    product_model: str
    product_id: str
    stock_quantity: int
    sold_quantity: int = 0
    expected_arrival: Optional[dt.date] = None

    def to_excel_row(self) -> List[str]:
        arrival = self.expected_arrival.strftime("%Y-%m-%d") if self.expected_arrival else ""
        return [
            self.product_type,
            self.manufacturer,
            self.product_name,
            self.product_model,
            self.product_id,
            str(self.stock_quantity),
            str(self.sold_quantity),
            INVENTORY_STATUS_LABEL_NORMAL,
            arrival,
        ]


@dataclass
class OrderRow:
    customer_type: str
    customer_name: str
    sales: str
    order_id: str
    tracking_number: str
    status: str
    order_time: dt.datetime
    payment_time: Optional[dt.datetime]
    ship_deadline: Optional[dt.datetime]
    product_id: str
    quantity: int
    return_request_id: str = ""

    def to_excel_row(self) -> List[str]:
        payment_str = self.payment_time.strftime("%Y-%m-%d %H:%M:%S") if self.payment_time else ""
        ship_deadline_str = self.ship_deadline.strftime("%Y-%m-%d %H:%M:%S") if self.ship_deadline else ""
        return [
            self.customer_type,
            self.customer_name,
            self.sales,
            self.order_id,
            self.tracking_number or "",
            self.status,
            self.order_time.strftime("%Y-%m-%d %H:%M:%S"),
            payment_str,
            ship_deadline_str,
            self.product_id,
            str(self.quantity),
            self.return_request_id,
        ]

    def hash_value(self) -> str:
        ship_deadline_str = self.ship_deadline.strftime("%Y-%m-%d %H:%M:%S") if self.ship_deadline else ""
        raw = (
            self.order_id
            + self.product_id
            + self.customer_type
            + self.sales
            + self.customer_name
            + ship_deadline_str
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_sql(self) -> str:
        payment_literal = (
            f"'{self.payment_time.strftime('%Y-%m-%d %H:%M:%S')}'" if self.payment_time else "NULL"
        )
        ship_deadline_literal = (
            f"'{self.ship_deadline.strftime('%Y-%m-%d %H:%M:%S')}'" if self.ship_deadline else "NULL"
        )
        status_value = ORDER_STATUS_TO_INT.get(self.status, ORDER_STATUS_TO_INT["新建"])
        customer_type_value = CUSTOMER_TYPE_TO_INT.get(self.customer_type, CUSTOMER_TYPE_TO_INT["未知"])
        return (
            "INSERT INTO `order` "
            "(`Hash`,`customer_type`,`customer_name`,`sales`,`order_id`,`tracking_number`,"
            "`status`,`order_time`,`payment_time`,`ship_deadline`,`product_id`,`quantity`,"
            "`return_request_id`,`customer_id`,`created_by_id`,`created_at`,`updated_at`) VALUES ("
            f"'{self.hash_value()}',"
            f"{customer_type_value},"
            f"'{escape_sql(self.customer_name)}',"
            f"'{escape_sql(self.sales)}',"
            f"'{escape_sql(self.order_id)}',"
            f"'{escape_sql(self.tracking_number or '')}',"
            f"{status_value},"
            f"'{self.order_time.strftime('%Y-%m-%d %H:%M:%S')}',"
            f"{payment_literal},"
            f"{ship_deadline_literal},"
            f"'{escape_sql(self.product_id)}',"
            f"{self.quantity},"
            f"'{escape_sql(self.return_request_id)}',"
            "'','',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);"
        )


def build_products(rng: random.Random) -> List[InventoryItem]:
    products: List[InventoryItem] = []
    for blueprint in PRODUCT_BLUEPRINTS:
        products.append(
            InventoryItem(
                product_type=blueprint["product_type"],
                manufacturer=blueprint["manufacturer"],
                product_name=blueprint["product_name"],
                product_model=blueprint["product_model"],
                product_id=hashlib.sha256(("["+blueprint["manufacturer"]+"]"+blueprint["product_name"]+"#"+blueprint["product_model"]).encode("utf-8")).hexdigest()[:16],
                stock_quantity=0,
                sold_quantity=0,
                expected_arrival=dt.date.today() + dt.timedelta(days=rng.randint(*EXPECTED_ARRIVAL_DAYS_RANGE))
                if rng.random() < EXPECTED_ARRIVAL_PROBABILITY
                else None,
            )
        )
    return products


ONLINE_ORDER_STATUSES: Tuple[str, ...] = (
    "新建",
    "待付款",
    "待发货",
    "打包中",
    "待收货",
    "完成",
    "暂停",
    "取消",
    "退货申请中",
    "退货驳回",
    "退货中",
)

OFFLINE_ORDER_STATUSES: Tuple[str, ...] = (
    "完成",
    "退货申请中",
    "退货驳回",
    "退货中",
)

ONLINE_TRACKING_RELEVANT_STATUSES: Tuple[str, ...] = (
    "待收货",
    "完成",
    "退货申请中",
    "退货驳回",
    "退货中",
)


def random_online_username(rng: random.Random, length: int = 12) -> str:
    """生成仅包含字母+数字的随机用户名（可复现：只依赖 rng）。"""
    raw = f"user-{rng.getrandbits(256):064x}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    alphabet = string.ascii_lowercase + string.digits
    return "".join(alphabet[b % len(alphabet)] for b in digest)[:length]


def pick_customer(rng: random.Random, order_type: str) -> str:
    if order_type == "online":
        return random_online_username(rng)
    pool = CUSTOMER_POOLS.get("offline", [])
    if not pool:
        return "线下客户"
    return rng.choice(pool)


def pick_order_status(
    rng: random.Random,
    order_type: str,
    online_status_weights: Dict[str, float],
    offline_status_weights: Dict[str, float],
) -> str:
    """按固定比例随机生成订单状态（不包含“未知”）。"""
    if order_type == "offline":
        return weighted_choice(rng, offline_status_weights)
    return weighted_choice(rng, online_status_weights)




def generate_orders(
    total_orders: int,
    order_type_weights: Dict[str, float],
    sales_weights: Dict[str, float],
    products: List[InventoryItem],
    rng: random.Random,
    online_status_weights: Dict[str, float],
    offline_status_weights: Dict[str, float],
) -> Tuple[List[OrderRow], Dict[str, int]]:
    orders: List[OrderRow] = []
    product_totals: Dict[str, int] = {p.product_id: 0 for p in products}

    for index in range(total_orders):
        order_type = weighted_choice(rng, order_type_weights)
        if order_type not in ("online", "offline"):
                                               
            order_type = "online"

        order_prefix = ORDER_PREFIX_MAP.get(order_type, "UNK")
        order_time = dt.datetime.now() - dt.timedelta(
            days=rng.randint(*ORDER_TIME_DAYS_RANGE),
            hours=rng.randint(*ORDER_TIME_HOURS_RANGE),
        )

        status = pick_order_status(rng, order_type, online_status_weights, offline_status_weights)

                     
        if order_type == "offline":
            product_count = rng.randint(1, min(len(products), OFFLINE_PRODUCT_MAX))
            quantity_range = OFFLINE_QUANTITY_RANGE
        else:
            product_count = rng.randint(ONLINE_PRODUCT_RANGE[0], min(len(products), ONLINE_PRODUCT_RANGE[1]))
            quantity_range = ONLINE_QUANTITY_RANGE

        product_choices = rng.sample(products, k=product_count)

        customer_type = CUSTOMER_TYPE_LABELS[order_type]
        sales = weighted_choice(rng, sales_weights)
        customer_name = pick_customer(rng, order_type)

        order_id = f"{order_prefix}-{order_time.strftime('%Y%m%d%H%M%S')}-{rng.randint(ORDER_ID_RANDOM_MIN, ORDER_ID_RANDOM_MAX)}-{index:04d}"

                                     
        if order_type == "offline":
            tracking_number = ""
            ship_deadline = None
            payment_time = order_time           
        else:
            ship_deadline = order_time + dt.timedelta(days=rng.randint(*SHIP_DEADLINE_DAYS_RANGE))

                                   
            if status in ("新建", "待付款"):
                payment_time = None
            else:
                payment_time = order_time + dt.timedelta(minutes=rng.randint(*PAYMENT_DELAY_MINUTES))

            tracking_number = (
                f"{TRACKING_PREFIX}{rng.randint(TRACKING_RANDOM_MIN, TRACKING_RANDOM_MAX)}"
                if status in ONLINE_TRACKING_RELEVANT_STATUSES
                else ""
            )

                                   
        for product in product_choices:
            quantity = rng.randint(*quantity_range)
            product_totals[product.product_id] += quantity

            return_request_id = ""
            if status in ("退货申请中", "退货中"):
                return_request_id = f"RR-{uuid.uuid4().hex[:10].upper()}"

            orders.append(
                OrderRow(
                    customer_type=customer_type,
                    customer_name=customer_name,
                    sales=sales,
                    order_id=order_id,
                    tracking_number=tracking_number,
                    status=status,
                    order_time=order_time,
                    payment_time=payment_time,
                    ship_deadline=ship_deadline,
                    product_id=product.product_id,
                    quantity=quantity,
                    return_request_id=return_request_id,
                )
            )
    return orders, product_totals


def adjust_inventory_levels(products: List[InventoryItem], product_totals: Dict[str, int]) -> None:
    for product in products:
        total = product_totals.get(product.product_id, 0)
        buffer = max(random.randint(random.randint(1,50),random.randint(51,99)), total // 2)
        product.sold_quantity = total
        product.stock_quantity = total + buffer


def write_orders_excel(rows: Iterable[OrderRow], path: Path) -> None:
    workbook_cls = _require_workbook()
    wb = workbook_cls()
    ws = wb.active
    ws.title = "Orders"
    ws.append(ORDER_HEADERS)
    for row in rows:
        ws.append(row.to_excel_row())
    wb.save(path)


def write_inventory_excel(items: Iterable[InventoryItem], path: Path) -> None:
    workbook_cls = _require_workbook()
    wb = workbook_cls()
    ws = wb.active
    ws.title = "Inventory"
    ws.append(INVENTORY_HEADERS)
    for item in items:
        ws.append(item.to_excel_row())
    wb.save(path)


def write_order_sql(rows: Iterable[OrderRow], path: Path) -> None:
    lines = [
        "-- Auto generated order data",
        "BEGIN;",
    ]
    for row in rows:
        lines.append(row.to_sql())
    lines.append("COMMIT;")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_inventory_sql(items: Iterable[InventoryItem], path: Path) -> None:
    lines = [
        "-- Auto generated inventory seed data",
        "BEGIN;",
    ]
    for item in items:
        expected = f"'{item.expected_arrival.strftime('%Y-%m-%d')}'" if item.expected_arrival else "NULL"
        lines.append(
            "INSERT INTO `inventory` "
            "(`product_id`,`product_type`,`manufacturer`,`product_name`,`product_model`,"
            "`stock_quantity`,`sold_quantity`,`status`,`expected_arrival`,`created_at`,`updated_at`) VALUES ("
            f"'{escape_sql(item.product_id)}',"
            f"'{escape_sql(item.product_type)}',"
            f"'{escape_sql(item.manufacturer)}',"
            f"'{escape_sql(item.product_name)}',"
            f"'{escape_sql(item.product_model)}',"
            f"{item.stock_quantity},"
            f"{item.sold_quantity},"
            f"{INVENTORY_NORMAL_STATUS},"
            f"{expected},"
            "CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);"
        )
    lines.append("COMMIT;")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_sales_weights(raw: Optional[str]) -> Dict[str, float]:
    if not raw:
        return normalize_weights(DEFAULT_SALES_WEIGHTS)
    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError("sales-ratio 必须是 JSON 对象")
    return normalize_weights({str(k): float(v) for k, v in loaded.items()})


def parse_status_weights(
    raw: Optional[str],
    allowed_statuses: Sequence[str],
    default_weights: Dict[str, float],
    arg_name: str,
) -> Dict[str, float]:
    """解析订单状态权重（JSON dict），并按 allowed_statuses 做校验与归一化。"""
    if not raw:
        base = {status: float(default_weights.get(status, 0.0)) for status in allowed_statuses}
        return normalize_weights(base)

    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError(f"{arg_name} 必须是 JSON 对象")

    allowed_set = set(allowed_statuses)
    unknown = [str(k) for k in loaded.keys() if str(k) not in allowed_set]
    if unknown:
        raise ValueError(f"{arg_name} 包含不支持的状态：{unknown}；允许的状态为：{list(allowed_statuses)}")

    base = {status: float(loaded.get(status, 0.0)) for status in allowed_statuses}
    return normalize_weights(base)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成订单 Excel 及订单/库存 SQL")
    parser.add_argument("--total-orders", type=int, default=120, help="生成的订单数量（按比例分配到两类客户）")
    parser.add_argument("--online-ratio", type=float, default=0.3, help="线上预订订单占比")
    parser.add_argument("--offline-ratio", type=float, default=0.7, help="线下零售订单占比")
    parser.add_argument(
        "--sales-ratio",
        type=str,
        default="",
        help='销售员占比，JSON 形式，如 {"张三":0.4,"李四":0.6}。线上/线下统一随机分配。',
    )
    parser.add_argument(
        "--online-status-ratio",
        type=str,
        default="",
        help='线上订单状态占比，JSON 形式，如 {"完成":0.5,"待收货":0.2,"待发货":0.1,"待付款":0.1,"新建":0.1}；未提供则使用默认分布。',
    )
    parser.add_argument(
        "--offline-status-ratio",
        type=str,
        default="",
        help='线下订单状态占比，JSON 形式，如 {"完成":0.85,"退货申请中":0.1,"退货中":0.03,"退货驳回":0.02}；未提供则使用默认分布。',
    )
    parser.add_argument("--seed", type=int, default=int(time.time()), help="随机种子，确保结果可复现")
    parser.add_argument("--output-dir", type=Path, default=Path("gen_data_output"), help="输出目录")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    order_type_weights = normalize_weights({"online": args.online_ratio, "offline": args.offline_ratio})
    sales_weights = parse_sales_weights(args.sales_ratio)

    online_status_weights = parse_status_weights(
        args.online_status_ratio,
        ONLINE_ORDER_STATUSES,
        DEFAULT_ONLINE_STATUS_WEIGHTS,
        "online-status-ratio",
    )
    offline_status_weights = parse_status_weights(
        args.offline_status_ratio,
        OFFLINE_ORDER_STATUSES,
        DEFAULT_OFFLINE_STATUS_WEIGHTS,
        "offline-status-ratio",
    )

    products = build_products(rng)
    orders, product_totals = generate_orders(args.total_orders, order_type_weights, sales_weights, products, rng, online_status_weights, offline_status_weights)
    adjust_inventory_levels(products, product_totals)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")

    order_excel = args.output_dir / f"orders_{timestamp}.xlsx"
    inventory_excel = args.output_dir / f"inventory_{timestamp}.xlsx"
    order_sql = args.output_dir / f"orders_{timestamp}.sql"
    inventory_sql = args.output_dir / f"inventory_{timestamp}.sql"

    write_orders_excel(orders, order_excel)
    write_inventory_excel(products, inventory_excel)
                                       
                                                 

    print(f"生成完成，订单行数：{len(orders)}")
    print(f"订单 Excel：{order_excel}")
    print(f"库存 Excel：{inventory_excel}")
    print(f"订单 SQL：{order_sql}")
    print(f"库存 SQL：{inventory_sql}")


if __name__ == "__main__":
    main()