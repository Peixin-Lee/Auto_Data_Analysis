"""
数据可视化生成器
根据结构化数据和用户问题生成 HTML 数据分析报告
采用模板化方案：LLM 只负责数据提取和图表配置，HTML 由预设模板生成
"""
import json
import os
import re
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

# ==================== 配置 ====================
# 从环境变量读取配置（请在 .env 文件中配置）
API_KEY = os.getenv("VISUALIZER_API_KEY")
API_BASE = os.getenv("VISUALIZER_API_BASE")
MODEL_NAME = os.getenv("VISUALIZER_MODEL_NAME")

# ==================== 数据模型 ====================
class KPIMetric(BaseModel):
    """KPI指标"""
    label: str = Field(description="指标名称，如'基金规模'")
    value: float = Field(description="数值")
    unit: str = Field(description="单位，如'元'、'%'")
    format: Optional[str] = Field(default="number", description="格式化方式：number/percent/currency")

class ChartData(BaseModel):
    """图表数据配置"""
    chart_id: str = Field(description="图表唯一标识，如'chart_1'")
    title: str = Field(description="图表标题")
    chart_type: Literal["line", "bar", "pie", "area", "scatter"] = Field(description="图表类型")
    categories: Optional[List[str]] = Field(default=None, description="X轴类别，适用于折线图/柱状图")
    series: List[Dict[str, Any]] = Field(description="数据系列列表，每个系列包含name和data")
    unit: Optional[str] = Field(default="", description="数值单位")
    note: Optional[str] = Field(default="", description="图表注释")

class ReportData(BaseModel):
    """报告数据（LLM输出）"""
    title: str = Field(description="报告标题")
    summary: str = Field(description="分析摘要，3-7条要点")
    kpis: List[KPIMetric] = Field(description="KPI指标列表，0-6个")
    charts: List[ChartData] = Field(description="图表配置列表")

class HTMLReport(BaseModel):
    """最终HTML报告"""
    html: str = Field(description="完整的HTML代码")
    title: str = Field(description="报告标题")
    summary: str = Field(description="分析摘要")

# ==================== HTML 模板 ====================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #fff;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            color: #00d4ff;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
            margin-bottom: 15px;
        }}
        
        .summary {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }}
        
        .summary h2 {{
            color: #00d4ff;
            font-size: 1.5em;
            margin-bottom: 15px;
        }}
        
        .summary-content {{
            line-height: 1.8;
            white-space: pre-wrap;
            color: rgba(255, 255, 255, 0.9);
        }}
        
        .kpi-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .kpi-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.3);
            border-color: #00d4ff;
        }}
        
        .kpi-label {{
            font-size: 0.9em;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 10px;
        }}
        
        .kpi-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #00d4ff;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
            word-break: break-word;
            line-height: 1.2;
        }}

        .kpi-unit {{
            font-size: 0.9em;
            color: rgba(255, 255, 255, 0.6);
            margin-top: 8px;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 25px;
        }}
        
        .chart-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }}
        
        .chart-card:hover {{
            border-color: rgba(0, 212, 255, 0.5);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }}
        
        .chart-title {{
            font-size: 1.2em;
            color: #00d4ff;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .chart-container {{
            width: 100%;
            height: 400px;
        }}
        
        .chart-note {{
            margin-top: 10px;
            font-size: 0.85em;
            color: rgba(255, 255, 255, 0.6);
            font-style: italic;
        }}
        
        .export-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            z-index: 1000;
        }}
        
        .export-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}
        
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            .header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <button class="export-btn" onclick="exportReport()">📥 导出报告</button>
    
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
        </div>
        
        <div class="summary">
            <h2>📊 分析摘要</h2>
            <div class="summary-content">{summary}</div>
        </div>
        
        <div class="kpi-section" id="kpi-section">
            <!-- KPI 指标将由 JS 动态生成 -->
        </div>
        
        <div class="charts-grid" id="charts-grid">
            <!-- 图表将由 JS 动态生成 -->
        </div>
    </div>
    
    <script>
        const reportData = {report_data};
        const chartInstances = [];
        
        // 渲染 KPI 指标
        function renderKPIs() {{
            const kpiSection = document.getElementById('kpi-section');
            if (!reportData.kpis || reportData.kpis.length === 0) {{
                kpiSection.style.display = 'none';
                return;
            }}
            
            reportData.kpis.forEach(kpi => {{
                const card = document.createElement('div');
                card.className = 'kpi-card';
                
                let displayValue = kpi.value;
                if (kpi.format === 'percent') {{
                    displayValue = (kpi.value * 100).toFixed(2);
                    // 确保百分比单位存在
                    if (!kpi.unit) {{
                        kpi.unit = '%';
                    }}
                }} else if (kpi.format === 'currency') {{
                    displayValue = kpi.value.toLocaleString('zh-CN');
                }} else {{
                    displayValue = kpi.value.toLocaleString('zh-CN');
                }}
                
                card.innerHTML = `
                    <div class="kpi-label">${{kpi.label}}</div>
                    <div class="kpi-value">${{displayValue}}</div>
                    <div class="kpi-unit">${{kpi.unit}}</div>
                `;
                
                kpiSection.appendChild(card);
            }});
        }}
        
        // 渲染图表
        function renderCharts() {{
            const chartsGrid = document.getElementById('charts-grid');
            
            reportData.charts.forEach((chartConfig, index) => {{
                // 创建图表容器
                const card = document.createElement('div');
                card.className = 'chart-card';
                
                const chartContainer = document.createElement('div');
                chartContainer.className = 'chart-container';
                chartContainer.id = chartConfig.chart_id || `chart_${{index}}`;
                
                card.innerHTML = `
                    <div class="chart-title">${{chartConfig.title}}</div>
                `;
                card.appendChild(chartContainer);
                
                if (chartConfig.note) {{
                    const note = document.createElement('div');
                    note.className = 'chart-note';
                    note.textContent = chartConfig.note;
                    card.appendChild(note);
                }}
                
                chartsGrid.appendChild(card);
                
                // 初始化 ECharts
                const chart = echarts.init(chartContainer);
                chartInstances.push(chart);
                
                // 构建 ECharts 配置
                const option = buildChartOption(chartConfig);
                chart.setOption(option);
            }});
        }}
        
        // 构建 ECharts 配置
        function buildChartOption(config) {{
            const baseOption = {{
                backgroundColor: 'transparent',
                tooltip: {{
                    trigger: config.chart_type === 'pie' ? 'item' : 'axis',
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    borderColor: '#00d4ff',
                    borderWidth: 1,
                    textStyle: {{ color: '#fff' }}
                }},
                grid: {{
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    top: '10%',
                    containLabel: true
                }},
                animation: true,
                animationDuration: 1000,
                animationEasing: 'cubicOut'
            }};
            
            if (config.chart_type === 'pie') {{
                return {{
                    ...baseOption,
                    series: [{{
                        type: 'pie',
                        radius: ['40%', '70%'],
                        center: ['50%', '50%'],
                        data: config.series[0].data.map((value, idx) => ({{
                            name: config.categories[idx],
                            value: value
                        }})),
                        itemStyle: {{
                            borderRadius: 8,
                            borderColor: '#0f0c29',
                            borderWidth: 2
                        }},
                        label: {{
                            color: '#fff',
                            fontSize: 12
                        }},
                        emphasis: {{
                            itemStyle: {{
                                shadowBlur: 10,
                                shadowOffsetX: 0,
                                shadowColor: 'rgba(0, 212, 255, 0.5)'
                            }}
                        }}
                    }}]
                }};
            }} else if (config.chart_type === 'line' || config.chart_type === 'area') {{
                return {{
                    ...baseOption,
                    xAxis: {{
                        type: 'category',
                        data: config.categories,
                        axisLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.3)' }} }},
                        axisLabel: {{ color: '#fff' }}
                    }},
                    yAxis: {{
                        type: 'value',
                        axisLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.3)' }} }},
                        axisLabel: {{ color: '#fff' }},
                        splitLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.1)' }} }}
                    }},
                    series: config.series.map(s => ({{
                        name: s.name,
                        type: config.chart_type === 'area' ? 'line' : 'line',
                        data: s.data,
                        smooth: true,
                        areaStyle: config.chart_type === 'area' ? {{ opacity: 0.3 }} : undefined,
                        lineStyle: {{ width: 3 }},
                        itemStyle: {{
                            borderWidth: 2,
                            borderColor: '#fff'
                        }},
                        emphasis: {{
                            itemStyle: {{
                                shadowBlur: 10,
                                shadowColor: 'rgba(0, 212, 255, 0.5)'
                            }}
                        }}
                    }})),
                    legend: {{
                        textStyle: {{ color: '#fff' }},
                        top: '5%'
                    }}
                }};
            }} else if (config.chart_type === 'bar') {{
                return {{
                    ...baseOption,
                    xAxis: {{
                        type: 'category',
                        data: config.categories,
                        axisLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.3)' }} }},
                        axisLabel: {{ color: '#fff', rotate: config.categories.length > 8 ? 45 : 0 }}
                    }},
                    yAxis: {{
                        type: 'value',
                        axisLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.3)' }} }},
                        axisLabel: {{ color: '#fff' }},
                        splitLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.1)' }} }}
                    }},
                    series: config.series.map(s => ({{
                        name: s.name,
                        type: 'bar',
                        barMaxWidth: 60,
                        data: s.data,
                        itemStyle: {{
                            borderRadius: [8, 8, 0, 0],
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                {{ offset: 0, color: '#00d4ff' }},
                                {{ offset: 1, color: '#667eea' }}
                            ])
                        }},
                        emphasis: {{
                            itemStyle: {{
                                shadowBlur: 10,
                                shadowColor: 'rgba(0, 212, 255, 0.5)'
                            }}
                        }}
                    }})),
                    legend: {{
                        textStyle: {{ color: '#fff' }},
                        top: '5%'
                    }}
                }};
            }}
            
            return baseOption;
        }}
        
        // 响应式调整
        window.addEventListener('resize', debounce(() => {{
            chartInstances.forEach(chart => chart.resize());
        }}, 200));
        
        function debounce(func, wait) {{
            let timeout;
            return function(...args) {{
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            }};
        }}
        
        // 导出报告
        function exportReport() {{
            const filename = '{title}_' + new Date().toISOString().slice(0, 10) + '.html';
            const blob = new Blob([document.documentElement.outerHTML], {{ type: 'text/html' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        }}
        
        // 初始化页面
        renderKPIs();
        renderCharts();
    </script>
</body>
</html>
"""

# ==================== 知识库构建器 ====================
class KnowledgeBaseBuilder:
    """从 analyzed_result.json 构建知识库"""
    
    @staticmethod
    def build_context(analyzed_data: Dict[str, Any], max_tokens: int = 8000) -> str:
        """
        构建紧凑的上下文
        
        策略:
        1. 提取所有 tables
        2. 提取所有 key_points
        3. 按章节组织 summary
        """
        chunks = analyzed_data.get("analyzed_chunks", [])
        
        # 1. 收集所有表格
        all_tables = []
        for chunk in chunks:
            if "analysis" in chunk:
                analysis = chunk["analysis"]
                header_path = chunk.get("metadata", {}).get("header_path", "未知章节")
                
                for table in analysis.get("tables", []):
                    all_tables.append({
                        "section": header_path,
                        "table": table
                    })
        
        # 2. 收集所有关键点
        all_key_points = []
        for chunk in chunks:
            if "analysis" in chunk:
                header_path = chunk.get("metadata", {}).get("header_path", "未知章节")
                points = chunk["analysis"].get("key_points", [])
                for point in points:
                    all_key_points.append(f"[{header_path}] {point}")
        
        # 3. 收集章节摘要
        all_summaries = []
        for chunk in chunks:
            if "analysis" in chunk:
                header_path = chunk.get("metadata", {}).get("header_path", "未知章节")
                summary = chunk["analysis"].get("summary", "")
                if summary:
                    all_summaries.append(f"**{header_path}**: {summary}")
        
        # 4. 组装上下文
        context_parts = []
        
        # 表格部分 (最重要,放最前面)
        if all_tables:
            context_parts.append("# 📊 数据表格\n")
            for i, item in enumerate(all_tables[:20], 1):  # 限制20个表格
                table = item["table"]
                context_parts.append(f"## 表格 {i}: {table['title']}")
                context_parts.append(f"**章节**: {item['section']}")
                
                # 表格内容
                headers = " | ".join(table["headers"])
                context_parts.append(f"| {headers} |")
                context_parts.append(f"| {' | '.join(['---'] * len(table['headers']))} |")
                
                for row in table["rows"][:10]:  # 每个表格限制10行
                    context_parts.append(f"| {' | '.join(row)} |")
                
                if table.get("note"):
                    context_parts.append(f"*注: {table['note']}*")
                context_parts.append("")
        
        # 关键点部分
        if all_key_points:
            context_parts.append("\n# 🔑 关键要点\n")
            for point in all_key_points[:50]:  # 限制50个要点
                context_parts.append(f"- {point}")
        
        # 章节摘要部分
        if all_summaries:
            context_parts.append("\n# 📝 章节摘要\n")
            context_parts.append("\n".join(all_summaries[:30]))  # 限制30个摘要
        
        return "\n".join(context_parts)

# ==================== HTML报告生成器 ====================
class ReportGenerator:
    """生成HTML数据分析报告"""
    
    def __init__(self, api_key: str = API_KEY, base_url: str = API_BASE, model: str = MODEL_NAME):
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.2,
            max_tokens=8192,
        )
        
        self.output_parser = PydanticOutputParser(pydantic_object=ReportData)
        
        self.prompt = PromptTemplate(
            template="""你是一位专业的数据分析师，擅长从结构化数据中提取关键信息并生成图表配置。

# 任务
根据【用户问题】和【知识库数据】，输出结构化的报告数据配置（JSON格式）。

# 输出要求

## 1. 报告标题 (title)
- 根据用户问题和数据主题生成简洁的标题
- 中文，10-20字

## 2. 分析摘要 (summary)
- 针对用户问题，提取3-7条关键要点
- 包含具体数字、百分比、趋势等
- 每条要点用 "• " 开头，换行分隔
- 不要描述"HTML/图表如何实现"，只陈述数据结论

## 3. KPI指标 (kpis)
- 从数据中提取0-6个核心KPI指标
- 每个KPI包含：
  * label: 指标名称
  * value: 数值（浮点数）
  * unit: 单位（如"元"、"%"、"亿"）
  * format: 格式化方式，可选值：
    - "number": 普通数字
    - "percent": 百分比（value为小数，如0.25表示25%）
    - "currency": 货币（自动加千分位）

## 4. 图表配置 (charts)
- 根据数据生成3-10个图表
- **严禁编造数据**：只使用知识库中实际存在的数据
- 每个图表配置需包含：

### 必填字段
- chart_id: 唯一标识，如"chart_1"、"chart_2"
- title: 图表标题（简洁明确）
- chart_type: 图表类型，可选值：
  * "line": 折线图（适合趋势分析）
  * "bar": 柱状图（适合对比分析）
  * "pie": 饼图（适合占比分析）
  * "area": 面积图（适合填充趋势）
  * "scatter": 散点图（适合分布分析）

### 数据字段
- categories: X轴类别列表（折线图/柱状图需要），如["2022","2023","2024"]
- series: 数据系列列表，每个系列包含：
  * name: 系列名称
  * data: 数据数组（数值类型）
  
  示例1（单系列柱状图）：
  "series": [{{"name": "本期利润", "data": [31179560, -280792722, -452411765]}}]
  
  示例2（多系列折线图）：
  "series": [
    {{"name": "基金净值增长率", "data": [3.29, -13.35, -18.19]}},
    {{"name": "业绩基准", "data": [13.10, 8.60, 19.59]}}
  ]
  
  示例3（饼图）：
  "categories": ["股票", "债券", "现金"],
  "series": [{{"name": "占比", "data": [45.2, 36.1, 18.7]}}]

### 可选字段
- unit: 数值单位（如"%"、"元"、"万元"）
- note: 图表注释说明

## 5. 数据提取策略
- 优先提取表格中的数据（tables字段）
- 关键要点（key_points）可用于生成摘要
- 时间序列数据优先用折线图或面积图
- 对比类数据优先用柱状图
- 占比类数据优先用饼图
- 如果某类数据不存在，就跳过对应图表，**绝不允许使用示例数据或虚构数据**

# 输出格式
严格遵循以下JSON模式：
{format_instructions}

**注意**：直接输出JSON对象，不要添加任何前言、代码块标记或其他文字。

# 输入数据

## 用户问题
{user_query}

## 知识库数据
{knowledge_base}

现在开始输出纯JSON：""",
            input_variables=["user_query", "knowledge_base"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
        
        self.chain = self.prompt | self.llm
    
    def generate_report(self, analyzed_data: Dict[str, Any], user_query: str) -> HTMLReport:
        """
        生成HTML报告
        
        Args:
            analyzed_data: analyzer.py 输出的结果
            user_query: 用户问题 (如"分析2024年收益情况")
        
        Returns:
            HTMLReport 对象
        """
        # 构建知识库
        kb_builder = KnowledgeBaseBuilder()
        knowledge_base = kb_builder.build_context(analyzed_data)
        
        print(f"📊 知识库大小: {len(knowledge_base)} 字符")
        print(f"❓ 用户需求: {user_query}")
        
        # 调用LLM生成报告数据
        print("🤖 正在调用 LLM 提取数据...")
        result = self.chain.invoke({
            "user_query": user_query,
            "knowledge_base": knowledge_base
        })
        
        # 解析结果
        try:
            report_data = self.output_parser.parse(result.content)
        except Exception as e:
            print(f"⚠️ LLM输出解析失败: {e}")
            print(f"原始输出: {result.content[:500]}...")
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', result.content, re.DOTALL)
            if json_match:
                report_data = self.output_parser.parse(json_match.group())
            else:
                raise ValueError("无法从LLM输出中提取有效JSON")
        
        print(f"✅ 数据提取完成:")
        print(f"   - 标题: {report_data.title}")
        print(f"   - KPI数量: {len(report_data.kpis)}")
        print(f"   - 图表数量: {len(report_data.charts)}")
        
        # 使用模板生成HTML
        html = self._render_html(report_data)
        
        return HTMLReport(
            html=html,
            title=report_data.title,
            summary=report_data.summary
        )
    
    def _render_html(self, report_data: ReportData) -> str:
        """使用模板渲染HTML"""
        # 将 ReportData 转换为JSON字符串
        report_json = json.dumps(report_data.model_dump(), ensure_ascii=False, indent=2)
        
        # 填充模板
        html = HTML_TEMPLATE.format(
            title=report_data.title,
            summary=report_data.summary,
            report_data=report_json
        )
        
        return html

# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 测试用例
    sample_data = {
        "analyzed_chunks": [
            {
                "analysis": {
                    "summary": "测试数据",
                    "tables": [{
                        "title": "财务数据",
                        "headers": ["年份", "收入"],
                        "rows": [["2024", "100万"]]
                    }],
                    "key_points": ["测试点1"]
                },
                "metadata": {"header_path": "测试章节"}
            }
        ]
    }
    
    generator = ReportGenerator()
    report = generator.generate_report(sample_data, "生成测试报告")
    
    with open("test_report.html", "w", encoding="utf-8") as f:
        f.write(report.html)
    
    print("✅ 测试报告已生成：test_report.html")
