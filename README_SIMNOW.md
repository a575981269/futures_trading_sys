# SimNow 模拟环境使用指南

## 账户信息

- **经纪公司代码**: 9999
- **投资者代码**: 250969
- **手机号码**: 18317230715
- **用户昵称**: 你歪哥

## 配置步骤

### 1. 设置密码

SimNow 的交易密码是注册时设置的密码。请在 `.env` 文件中设置：

```env
CTP_PASSWORD=你的SimNow交易密码
```

### 2. 服务器地址

SimNow 的服务器地址已配置在 `.env` 文件中：

- **行情服务器**: `tcp://180.168.146.187:10010`
- **交易服务器**: `tcp://180.168.146.187:10000`

### 3. 运行测试

```bash
# 测试连接配置
python test_simnow.py

# 只测试行情接口
python test_simnow.py market

# 只测试交易接口
python test_simnow.py trading

# 全部测试
python test_simnow.py all
```

## 重要提示

### ⚠️ 当前状态

当前代码为**框架代码**，实际的 CTP 连接功能需要实现。系统提供了接口定义，但具体的 CTP API 调用需要：

1. **使用 CTP 封装库**（推荐）:
   - `vnpy-ctp`: VeighNa 框架的 CTP 接口
   - `pyctp`: Python 封装的 CTP 接口
   - 其他第三方封装库

2. **直接调用 CTP API**:
   - 需要 CTP 的 C++ 动态库文件
   - 使用 `ctypes` 调用 C++ 接口

### 📝 实现建议

#### 方案一：使用 vnpy-ctp（推荐）

```bash
pip install vnpy-ctp
```

然后在 `market_data/ctp_realtime.py` 和 `trading/ctp_trader.py` 中实现连接逻辑。

#### 方案二：使用 pyctp

```bash
pip install pyctp
```

#### 方案三：使用其他 CTP 封装库

根据你选择的库，实现相应的连接逻辑。

## SimNow 使用说明

### 1. 登录 SimNow 官网

访问 [SimNow 官网](http://www.simnow.com.cn/) 查看：
- 账户信息
- 服务器状态
- 使用文档

### 2. 密码重置

如果忘记密码，可以在 SimNow 官网重置。

### 3. 交易时间

SimNow 模拟环境的交易时间与实盘一致：
- **日盘**: 09:00 - 15:00
- **夜盘**: 21:00 - 02:30（部分品种）

### 4. 初始资金

SimNow 模拟账户通常有初始资金，可以在官网查看账户信息。

## 常见问题

### Q: 连接失败怎么办？

A: 检查以下几点：
1. 密码是否正确（在 `.env` 文件中设置）
2. 网络连接是否正常
3. SimNow 服务器是否正常（查看官网状态）
4. 是否在交易时间内

### Q: 如何查看账户信息？

A: 登录 SimNow 官网查看，或使用交易接口的 `query_account()` 方法。

### Q: 可以使用哪些合约？

A: SimNow 支持所有国内期货交易所的合约，包括：
- 上期所 (SHFE)
- 大商所 (DCE)
- 郑商所 (CZCE)
- 中金所 (CFFEX)
- 能源中心 (INE)

### Q: 如何获取合约代码？

A: 合约代码格式为：品种代码 + 年月
- 例如：`rb2501` (螺纹钢 2025年1月)
- 例如：`cu2501` (铜 2025年1月)

## 下一步

1. ✅ 配置 `.env` 文件中的密码
2. ⏳ 实现 CTP 连接逻辑（使用 vnpy-ctp 或其他库）
3. ⏳ 测试行情订阅
4. ⏳ 测试下单功能
5. ⏳ 集成到策略中

## 技术支持

- SimNow 官网: http://www.simnow.com.cn/
- SimNow 客服: 查看官网联系方式
- 系统文档: 查看 `ARCHITECTURE.md`

