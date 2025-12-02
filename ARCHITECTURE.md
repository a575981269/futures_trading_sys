# 量化交易系统完整架构文档

## 系统概述

本系统是一个完整的、成熟的量化交易系统，采用单体架构设计，所有模块在同一进程中运行。系统支持期货交易的回测、模拟交易和实盘交易。

## 系统架构

### 分层架构

```
┌─────────────────────────────────────────┐
│         API层 (api/)                    │
│  - RESTful API                          │
│  - WebSocket API                        │
│  - 策略管理API                           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        业务逻辑层                         │
│  - 策略引擎 (strategy/)                  │
│  - 交易引擎 (trading/)                   │
│  - 风控引擎 (risk/)                      │
│  - 任务调度 (scheduler/)                  │
│  - 监控管理 (monitor/)                   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        数据层                             │
│  - 市场数据 (market_data/)                │
│  - 数据库 (database/)                     │
│  - 指标计算 (indicators/)                 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        基础设施层                         │
│  - 配置 (config/)                        │
│  - 日志 (utils/logger.py)                │
│  - 工具 (utils/)                         │
└─────────────────────────────────────────┘
```

## 核心模块

### 1. 风控模块 (`risk/`)

**功能：**
- 持仓风控（单品种持仓限制、总持仓限制、持仓价值比例）
- 资金风控（单笔最大金额、日亏损限制、账户资金比例）
- 订单风控（下单频率限制、价格偏离检查）

**主要类：**
- `RiskManager`: 风控管理器，统一风控检查入口
- `PositionLimit`: 持仓限制
- `CapitalLimit`: 资金限制
- `OrderLimit`: 订单限制

**使用示例：**
```python
from risk import RiskManager, PositionLimit, CapitalLimit, OrderLimit

# 创建风控管理器
position_limit = PositionLimit(
    max_position_per_symbol=10,
    max_total_positions=5,
    max_position_value_ratio=0.3
)
capital_limit = CapitalLimit(
    max_order_amount=100000,
    max_daily_loss=50000,
    max_daily_loss_ratio=0.1
)
order_limit = OrderLimit(
    max_orders_per_minute=10,
    max_price_deviation_ratio=0.05
)

risk_manager = RiskManager(
    position_limit=position_limit,
    capital_limit=capital_limit,
    order_limit=order_limit
)

# 检查订单风险
result = risk_manager.check_order_risk(order, portfolio, current_price)
if not result.passed:
    print(f"风控失败: {result.reason}")
```

### 2. 实盘交易模块 (`trading/live_*`)

**功能：**
- CTP交易接口封装
- 订单状态管理
- 持仓同步
- 账户资金同步
- 异常处理与重连机制

**主要类：**
- `TradingInterface`: 交易接口抽象基类
- `CTPTrader`: CTP交易接口封装
- `LiveAccount`: 实盘账户管理
- `LiveTrader`: 实盘交易管理器

**使用示例：**
```python
from trading.live_trader import LiveTrader
from trading.ctp_trader import CTPTrader
from risk import RiskManager

# 创建交易接口
ctp_trader = CTPTrader()
ctp_trader.connect()

# 创建风控管理器
risk_manager = RiskManager(...)

# 创建实盘交易管理器
live_trader = LiveTrader(
    trading_interface=ctp_trader,
    risk_manager=risk_manager
)

live_trader.connect()
live_trader.add_strategy(MyStrategy, {"param1": 100})
live_trader.start()
```

### 3. 订单管理器 (`trading/order_manager.py`)

**功能：**
- 订单状态跟踪
- 订单查询与统计
- 订单历史管理
- 订单回调机制

**主要类：**
- `OrderManager`: 订单管理器

**使用示例：**
```python
from trading.order_manager import OrderManager

order_manager = OrderManager()
order_manager.add_order(order)
order_manager.update_order(order)

# 查询订单
active_orders = order_manager.get_active_orders()
stats = order_manager.get_order_statistics()
```

### 4. 监控模块 (`monitor/`)

**功能：**
- 策略性能监控（实时盈亏、胜率、最大回撤）
- 系统资源监控（CPU、内存、网络）
- 异常监控（连接断开、订单失败、数据异常）
- 告警通知（邮件、短信、Webhook）

**主要类：**
- `MonitorManager`: 监控管理器
- `PerformanceMonitor`: 性能监控
- `SystemMonitor`: 系统监控
- `AlertManager`: 告警管理器

**使用示例：**
```python
from monitor import MonitorManager, AlertLevel

monitor = MonitorManager(portfolio=portfolio)
monitor.start_monitoring()

# 触发告警
monitor.trigger_alert(
    AlertLevel.WARNING,
    "最大回撤超过20%",
    source="PerformanceMonitor"
)
```

### 5. 任务调度模块 (`scheduler/`)

**功能：**
- 定时任务（数据下载、策略启动/停止、报告生成）
- 任务队列（异步任务处理）
- 任务状态跟踪

**主要类：**
- `TaskScheduler`: 任务调度器
- `Task`: 任务对象

**使用示例：**
```python
from scheduler import TaskScheduler

scheduler = TaskScheduler()
scheduler.start()

# 添加定时任务
scheduler.add_periodic_task(
    name="daily_report",
    func=generate_report,
    interval=3600  # 每小时执行一次
)
```

### 6. Web API模块 (`api/`)

**功能：**
- RESTful API（策略管理、交易控制、数据查询）
- WebSocket实时推送（行情、订单、账户）
- API文档（Swagger/OpenAPI）

**主要路由：**
- `/api/strategy/*`: 策略管理API
- `/api/trading/*`: 交易API
- `/api/monitor/*`: 监控API
- `/api/data/*`: 数据查询API

**使用示例：**
```python
from api.app import create_app
import uvicorn

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 7. 指标计算库 (`indicators/`)

**功能：**
- 常用技术指标（MA、EMA、MACD、RSI、KDJ、布林带等）
- 指标计算优化（向量化计算）
- 指标缓存机制

**主要类：**
- `TechnicalIndicators`: 技术指标计算类
- `MA`, `EMA`, `SMA`: 均线指标
- `MACD`: MACD指标
- `RSI`: RSI指标
- `BollingerBands`: 布林带指标

**使用示例：**
```python
from indicators import TechnicalIndicators

# 计算MA
ma_values = TechnicalIndicators.ma(klines, period=20)

# 计算MACD
macd_data = TechnicalIndicators.macd(klines)

# 计算所有指标
all_indicators = TechnicalIndicators.calculate_all(klines)
```

### 8. 策略管理模块 (`strategy/manager.py`)

**功能：**
- 策略注册与发现
- 策略参数管理
- 策略生命周期管理（启动、暂停、停止）
- 多策略并发运行
- 策略性能统计

**主要类：**
- `StrategyManager`: 策略管理器

**使用示例：**
```python
from strategy.manager import StrategyManager

manager = StrategyManager()
manager.register_strategy("MyStrategy", MyStrategyClass)

# 创建策略实例
strategy_id = manager.create_strategy("MyStrategy", {"param1": 100})
manager.start_strategy(strategy_id)
```

### 9. 账户管理模块 (`account/`)

**功能：**
- 多账户管理（模拟账户、实盘账户）
- 账户切换
- 账户资金统计

**主要类：**
- `AccountManager`: 账户管理器
- `MultiAccount`: 多账户管理

**使用示例：**
```python
from account import MultiAccount

multi_account = MultiAccount()
multi_account.add_sim_account("sim1", initial_capital=1000000)
multi_account.add_live_account("live1", trading_interface)

# 切换账户
multi_account.switch_account("sim1")
```

## 数据流

```
市场数据流：
CTP接口 → DataHandler → Database
                    ↓
              Strategy Engine
                    ↓
              Risk Manager
                    ↓
              Trading Engine
                    ↓
              Order Manager → CTP接口
```

## 关键设计原则

1. **模块化设计**: 各模块独立，低耦合
2. **接口抽象**: 使用抽象基类定义接口
3. **异常处理**: 完善的异常捕获与处理
4. **日志记录**: 关键操作都有日志
5. **配置化**: 参数可配置，不硬编码
6. **可扩展性**: 易于添加新策略、新指标
7. **安全性**: 风控优先，安全第一

## 依赖包

主要依赖包已添加到 `requirements.txt`:
- FastAPI: Web API框架
- psutil: 系统监控
- APScheduler: 任务调度
- requests: HTTP请求

## 使用建议

1. **开发环境**: 使用模拟账户进行策略开发和测试
2. **风控配置**: 根据实际需求配置风控参数
3. **监控告警**: 设置合适的告警阈值和通知方式
4. **实盘交易**: 充分测试后再接入实盘，建议先小资金测试

## 后续扩展

系统架构支持以下扩展：
- 更多技术指标
- 更多数据源
- 更多交易接口
- 分布式部署（如需要）
- 机器学习集成
- 策略回测优化

