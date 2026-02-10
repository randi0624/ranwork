# ranwork

一个可根据**地理名称**查询天气的 Web 程序。

## 功能

- 输入地名（如：北京、上海、London）
- 后端先通过 Open-Meteo Geocoding API 解析地点坐标
- 再通过 Open-Meteo Forecast API 拉取实时天气与当日温度范围
- 页面展示温度、湿度、风速、天气描述、时区与坐标

> 天气数据来源：Open-Meteo 官方公开网站与 API
> https://open-meteo.com/

## 运行方式

```bash
python3 app.py
```

打开浏览器访问：

- http://127.0.0.1:8000

## 接口

- `GET /api/weather?place=北京`
