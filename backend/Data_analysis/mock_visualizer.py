#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟可视化服务 - 用于测试完整流程
"""
import json
from typing import Dict, Any
from datetime import datetime

class MockVisualizationResult:
    def __init__(self, html: str, title: str, summary: str):
        self.html = html
        self.title = title
        self.summary = summary

class MockReportGenerator:
    def __init__(self, api_key: str, base_url: str, model: str):
        # Mock implementation - doesn't use actual API
        pass

    def generate_report(self, analysis_result: Dict[str, Any], user_query: str) -> MockVisualizationResult:
        """生成模拟的可视化报告"""

        # 提取基本信息
        ocr_result = analysis_result.get('source', {})
        file_name = ocr_result.get('markdown', '').split('\n')[0] if ocr_result.get('markdown') else '文档'

        # 生成HTML报告
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.0/dist/echarts.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .chart {{
            height: 400px;
            margin: 20px 0;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .info-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 数据分析报告</h1>
            <p>基于文档内容的智能分析与可视化</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>📄 文档信息</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>文件名称</h3>
                        <p>{file_name}</p>
                    </div>
                    <div class="info-card">
                        <h3>分析时间</h3>
                        <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    <div class="info-card">
                        <h3>处理状态</h3>
                        <p>✅ 分析完成</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📈 销售趋势分析</h2>
                <div id="salesChart" class="chart"></div>
            </div>

            <div class="section">
                <h2>📊 增长率分析</h2>
                <div id="growthChart" class="chart"></div>
            </div>

            <div class="section">
                <h2>🥧 产品分布</h2>
                <div id="pieChart" class="chart"></div>
            </div>

            <div class="section">
                <h2>🔍 关键洞察</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>趋势分析</h3>
                        <p>销售额呈现稳定增长趋势，5-6月增长显著加速</p>
                    </div>
                    <div class="info-card">
                        <h3>产品表现</h3>
                        <p>产品A是主要收入来源，占据35%的市场份额</p>
                    </div>
                    <div class="info-card">
                        <h3>增长潜力</h3>
                        <p>整体市场反应积极，具备进一步增长空间</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="timestamp">
            <p>报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
    </div>

    <script>
        // 销售额趋势图
        var salesChart = echarts.init(document.getElementById('salesChart'));
        var salesOption = {{
            title: {{
                text: '月度销售额趋势',
                left: 'center'
            }},
            tooltip: {{
                trigger: 'axis'
            }},
            xAxis: {{
                type: 'category',
                data: ['1月', '2月', '3月', '4月', '5月', '6月']
            }},
            yAxis: {{
                type: 'value',
                name: '销售额（万元）'
            }},
            series: [{{
                name: '销售额',
                type: 'bar',
                data: [4200, 5800, 7200, 6800, 8900, 9500],
                itemStyle: {{
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{{
                        offset: 0,
                        color: '#667eea'
                    }}, {{
                        offset: 1,
                        color: '#764ba2'
                    }}])
                }}
            }}]
        }};
        salesChart.setOption(salesOption);

        // 增长率图
        var growthChart = echarts.init(document.getElementById('growthChart'));
        var growthOption = {{
            title: {{
                text: '月度增长率',
                left: 'center'
            }},
            tooltip: {{
                trigger: 'axis'
            }},
            xAxis: {{
                type: 'category',
                data: ['1月', '2月', '3月', '4月', '5月', '6月']
            }},
            yAxis: {{
                type: 'value',
                name: '增长率（%）'
            }},
            series: [{{
                name: '增长率',
                type: 'line',
                data: [12, 19, 25, 22, 31, 35],
                smooth: true,
                lineStyle: {{
                    color: '#ff6b6b',
                    width: 3
                }},
                areaStyle: {{
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{{
                        offset: 0,
                        color: 'rgba(255, 107, 107, 0.3)'
                    }}, {{
                        offset: 1,
                        color: 'rgba(255, 107, 107, 0.1)'
                    }}])
                }}
            }}]
        }};
        growthChart.setOption(growthOption);

        // 产品分布饼图
        var pieChart = echarts.init(document.getElementById('pieChart'));
        var pieOption = {{
            title: {{
                text: '产品销售分布',
                left: 'center'
            }},
            tooltip: {{
                trigger: 'item',
                formatter: '{{a}} <br/>{{b}}: {{c}}% ({{d}}%)'
            }},
            series: [{{
                name: '产品分布',
                type: 'pie',
                radius: '60%',
                data: [
                    {{value: 35, name: '产品A'}},
                    {{value: 28, name: '产品B'}},
                    {{value: 22, name: '产品C'}},
                    {{value: 15, name: '产品D'}}
                ],
                emphasis: {{
                    itemStyle: {{
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }}
                }}
            }}]
        }};
        pieChart.setOption(pieOption);

        // 响应式调整
        window.addEventListener('resize', function() {{
            salesChart.resize();
            growthChart.resize();
            pieChart.resize();
        }});
    </script>
</body>
</html>
        """

        return MockVisualizationResult(
            html=html_content,
            title="数据分析报告",
            summary="基于文档内容生成的数据分析报告，包含销售额趋势、增长率分析和产品分布可视化图表。报告展示了6个月的销售数据，呈现稳定增长趋势。"
        )