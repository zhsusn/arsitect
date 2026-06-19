"""Tests for PageSpecResolver."""

from __future__ import annotations

from app.services.page_spec_resolver import (
    _infer_page_type,
    _parse_mermaid_flowchart,
    parse_module_requirements,
)

SAMPLE_DR001 = (
    "# DR-001：项目工作台（Project Dashboard）模块详细需求\n\n"
    "> **模块编号**：DR-001\n"
    "> **模块名称**：项目工作台（Project Dashboard）\n"
    "> **关联需求**：REQ-P0-001\n"
    "> **关联用户故事**：US-001（创建与管理项目）\n"
    "> **版本**：v1.0\n"
    "> **状态**：Draft\n\n"
    "---\n\n"
    "## 2. 原型与页面结构\n\n"
    "### 2.1 页面清单\n\n"
    "| 页面名称 | URL/入口 | 职责 |\n"
    "|:---------|:---------|:-----|\n"
    "| 项目工作台主页 | `/projects` | 项目列表、健康度卡片 |\n"
    '| 新建项目弹窗 | 工作台主页 → 点击"+ 新建项目" | 分步向导 |\n'
    "| 项目详情侧滑面板 | 工作台主页 → 点击项目卡片 | 展示项目元数据 |\n\n"
    "### 2.4 页面跳转图\n\n"
    "```mermaid\n"
    "flowchart LR\n"
    '    subgraph SDLC_Visualizer["项目工作台域"]\n'
    '        Pg_Dashboard["项目工作台主页<br>/app/{appId}/dashboard"]\n'
    '        Pg_NewProjectModal["新建项目弹窗"]\n'
    '        Pg_ProjectDetailDrawer["项目详情侧滑面板"]\n'
    "    end\n\n"
    '    Pg_Dashboard -->|点击"新建项目"| Pg_NewProjectModal\n'
    "    Pg_Dashboard -->|点击项目卡片| Pg_ProjectDetailDrawer\n"
    "    Pg_NewProjectModal -.->|点击关闭/取消| Pg_Dashboard\n"
    "```\n\n"
    "---\n\n"
    "## 3. 输入输出字段\n\n"
    "### 3.1 用户输入字段表\n\n"
    "| 字段名 | 所属页面/步骤 | 类型 | 必填 | 校验规则 | 示例值 |\n"
    "|:-------|:-------------|:----:|:----:|:---------|:-------|\n"
    '| project_name | 新建项目-步骤① | 文本 | 是 | 1-64 字符 | "电商订单系统重构" |\n'
    '| project_description | 新建项目-步骤① | 多行文本 | 否 | 0-256 字符 | "基于 React 19 的前端重构项目" |\n'
    '| template_level | 新建项目-步骤② | 单选 | 是 | 枚举：Trivial / Light / Standard / Deep | "Standard" |\n'
    '| search_keyword | 工作台主页 | 文本 | 否 | 0-64 字符 | "订单" |\n\n'
    "---\n\n"
    "## 5. 交互规格\n\n"
    "### 5.1 按钮级交互状态机\n\n"
    "#### 页面：项目工作台主页（Pg_Dashboard）\n\n"
    "##### 元素：新建项目按钮（#btn-new-project）\n\n"
    "| 属性 | 说明 |\n"
    "|:-----|:-----|\n"
    "| 触发方式 | click |\n"
    "| 成功结果 | 新建项目弹窗（Pg_NewProjectModal）正常加载 |\n\n"
    "#### 页面：新建项目弹窗（Pg_NewProjectModal）\n\n"
    "##### 元素：确认创建按钮（#btn-confirm-create）\n\n"
    "| 属性 | 说明 |\n"
    "|:-----|:-----|\n"
    "| 触发方式 | click |\n"
    "| 成功结果 | 弹窗关闭，工作台列表首位新增项目卡片 |\n"
)


class TestInferPageType:
    """Test page type inference."""

    def test_dashboard(self) -> None:
        assert _infer_page_type("项目工作台主页", "概览") == "DASHBOARD"

    def test_modal(self) -> None:
        assert _infer_page_type("新建项目弹窗", "弹窗") == "MODAL"

    def test_list(self) -> None:
        assert _infer_page_type("项目列表页", "表格") == "LIST"

    def test_wizard(self) -> None:
        assert _infer_page_type("新建向导", "步骤") == "WIZARD"

    def test_form_default(self) -> None:
        assert _infer_page_type("设置页面", "配置") == "FORM"


class TestParseMermaidFlowchart:
    """Test Mermaid flowchart parser."""

    def test_basic_parsing(self) -> None:
        mermaid = (
            'flowchart LR\n    Pg_A["主页"] -->|点击| Pg_B["详情"]\n    Pg_B -.->|返回| Pg_A\n'
        )
        nodes, edges = _parse_mermaid_flowchart(mermaid)
        assert "主页" in nodes
        assert "详情" in nodes
        assert len(edges) == 2
        assert edges[0].source == "主页"
        assert edges[0].target == "详情"
        assert edges[0].label == "点击"
        assert edges[1].style == "dashed"

    def test_html_br_in_label(self) -> None:
        mermaid = 'Pg_Dash["项目工作台主页<br>/projects"]'
        nodes, _ = _parse_mermaid_flowchart(mermaid)
        assert any("项目工作台主页" in n for n in nodes)


class TestParseModuleRequirements:
    """Test full module-requirements.md parsing."""

    def test_header_metadata(self) -> None:
        spec = parse_module_requirements(SAMPLE_DR001)
        assert spec.module_id == "DR-001"
        assert spec.module_name == "项目工作台（Project Dashboard）"
        assert spec.related_stories == ["US-001"]

    def test_page_manifest(self) -> None:
        spec = parse_module_requirements(SAMPLE_DR001)
        assert len(spec.pages) == 3
        names = {p.page_name for p in spec.pages}
        assert "项目工作台主页" in names
        assert "新建项目弹窗" in names
        assert "项目详情侧滑面板" in names

    def test_page_types(self) -> None:
        spec = parse_module_requirements(SAMPLE_DR001)
        page_types = {p.page_name: p.page_type for p in spec.pages}
        assert page_types["项目工作台主页"] == "DASHBOARD"
        assert page_types["新建项目弹窗"] == "MODAL"

    def test_fields_attached(self) -> None:
        spec = parse_module_requirements(SAMPLE_DR001)
        modal = next(p for p in spec.pages if p.page_name == "新建项目弹窗")
        field_names = {f.name for f in modal.fields}
        assert "project_name" in field_names
        assert "template_level" in field_names

    def test_nav_edges(self) -> None:
        spec = parse_module_requirements(SAMPLE_DR001)
        assert len(spec.nav_edges) >= 2
        edge_labels = {e.label for e in spec.nav_edges}
        assert '点击"新建项目"' in edge_labels

    def test_page_nav_targets(self) -> None:
        spec = parse_module_requirements(SAMPLE_DR001)
        dashboard = next(p for p in spec.pages if p.page_name == "项目工作台主页")
        assert any("新建项目弹窗" in t for t in dashboard.nav_targets)

    def test_empty_content(self) -> None:
        spec = parse_module_requirements("")
        assert spec.module_id == ""
        assert spec.pages == []
