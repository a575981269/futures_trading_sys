# SimNow 配置快速指南

## 第一步：创建 .env 文件

在项目根目录创建 `.env` 文件，内容如下：

```env
# SimNow 模拟环境配置
CTP_BROKER_ID=9999
CTP_USER_ID=250969
CTP_PASSWORD=你的SimNow交易密码
CTP_MD_ADDRESS=tcp://180.168.146.187:10010
CTP_TRADE_ADDRESS=tcp://180.168.146.187:10000
CTP_APP_ID=simnow_client_test
CTP_AUTH_CODE=0000000000000000
```

**重要：** 请将 `CTP_PASSWORD` 替换为你的 SimNow 交易密码（注册时设置的密码）

## 第二步：运行测试

```bash
python test_simnow.py
```

## 账户信息总结

- **经纪公司代码**: 9999
- **投资者代码**: 250969  
- **行情服务器**: tcp://180.168.146.187:10010
- **交易服务器**: tcp://180.168.146.187:10000

## 注意事项

⚠️ **当前代码为框架代码**，实际的 CTP 连接需要实现。建议使用 `vnpy-ctp` 或其他 CTP 封装库。

详见 `README_SIMNOW.md` 获取更多信息。

