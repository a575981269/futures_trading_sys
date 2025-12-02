# 中国期货量化系统

一个基于CTP接口的中国期货量化交易系统，支持实时行情、历史行情和策略回测。

## 功能特性

- **实时行情**: 通过CTP接口订阅实时Tick和K线数据
- **历史行情**: 查询和存储历史K线数据
- **策略回测**: 完整的回测框架，支持逐Tick和逐Bar回测
- **模拟交易**: 虚拟盘模拟交易账户，支持实时行情驱动的策略交易
- **数据存储**: 使用SQLAlchemy管理历史数据
- **策略框架**: 预留策略接口，便于实现自定义策略

## 项目结构

```
duming/
├── config/                 # 配置管理
├── market_data/           # 行情数据模块
├── database/              # 数据库模块
├── strategy/              # 策略框架
├── backtest/              # 回测引擎
├── trading/               # 交易模块（模拟账户）
├── utils/                 # 工具类
├── main.py                # 主入口
└── requirements.txt       # 依赖包
```

## 安装

1. 安装Python 3.8或更高版本
2. 安装依赖包：
```bash
pip install -r requirements.txt
```

3. 配置CTP连接参数（编辑 `config/settings.py` 或使用环境变量）

## 使用说明

### 实时行情订阅

```python
from market_data.ctp_realtime import CTPRealtimeData

# 创建实时行情接口
realtime = CTPRealtimeData()
realtime.connect()
realtime.subscribe("rb2501")  # 订阅螺纹钢2501合约
```

### 历史行情查询

```python
from market_data.ctp_history import CTPHistoryData

# 创建历史行情接口
history = CTPHistoryData()
data = history.get_kline("rb2501", "1m", "2024-01-01", "2024-01-31")
```

### 策略回测

```python
from backtest.engine import BacktestEngine
from strategy.strategy_template import MyStrategy

# 创建回测引擎
engine = BacktestEngine()
engine.add_strategy(MyStrategy, {"param1": 100})
engine.set_data("rb2501", "2024-01-01", "2024-01-31")
engine.run_backtest()
```

### 模拟交易

```python
from trading.sim_trader import SimTrader
from trading.sim_account import SimAccount
from market_data.ctp_realtime import CTPRealtimeData
from strategy.strategy_template import MyStrategy

# 创建模拟账户
account = SimAccount(initial_capital=1000000.0)

# 创建模拟交易管理器
trader = SimTrader(account=account)
trader.add_strategy(MyStrategy, {"param1": 100})

# 连接实时行情
realtime = CTPRealtimeData()
realtime.connect()
trader.set_realtime_data(realtime)

# 启动模拟交易
trader.start()
realtime.subscribe("rb2501")
```

## 配置说明

系统配置位于 `config/settings.py`，包括：
- CTP连接参数（broker_id, user_id, password等）
- 数据库配置
- 日志配置

## 注意事项

- 需要配置正确的CTP连接参数才能使用实时行情
- 历史数据会自动存储到数据库中
- 策略实现需要继承 `BaseStrategy` 基类

## 开发计划

- [x] 项目结构搭建
- [x] 数据库模块
- [x] CTP行情接口
- [x] 策略框架
- [x] 回测引擎
- [x] 模拟交易账户
- [ ] 实盘交易接口（待开发）
- [ ] 风控模块（待开发）

