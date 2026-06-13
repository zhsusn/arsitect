"""DocForge document migration engine.

Encapsulates the logic previously in scripts/migrate_docs.py,
extract_c4_entities.py, inject_c4_tags.py and fill_dependencies.py
so it can be invoked both from CLI and from the Admin API.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------
DOC_TYPE_MAP: dict[str, str] = {
    "high-level-requirements": "PRD",
    "high-level-design": "ARCH",
    "detailed-requirements": "PRD",
    "detailed-design": "DETAIL_DESIGN",
    "interface-contracts": "API_DESIGN",
    "brainstorming": "CHANGELOG",
    "competitive-analysis": "CHANGELOG",
    "uat": "TEST_PLAN",
    "sign-off": "CHANGELOG",
    "code-review": "CHANGELOG",
}

DOC_TYPE_LEVEL_MAP: dict[str, str] = {
    "PRD": "L1",
    "DOMAIN_MODEL": "L2",
    "ARCH": "L2",
    "DETAIL_DESIGN": "L3",
    "API_DESIGN": "L3",
    "DB_DESIGN": "L2",
}

SPECIAL_FILES: dict[str, tuple[str, str]] = {
    "db-schema.md": ("DB_DESIGN", "L2"),
    "api-spec.md": ("API_DESIGN", "L3"),
}

_GENERIC_IDS = {
    "api", "service", "repository", "store", "manager",
    "engine", "handler", "controller", "router", "adapter",
    "dr-003", "dr-004", "dr-005", "dr-009", "dr-010", "dr-015",
}

# ------------------------------------------------------------------
# Result DTOs
# ------------------------------------------------------------------
@dataclass
class MigrationResult:
    migrated: list[tuple[str, str]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class C4RegistryResult:
    systems: int = 0
    actors: int = 0
    containers: int = 0
    components: int = 0
    interfaces: int = 0
    registry_path: str = ""


@dataclass
class C4TagResult:
    modified: int = 0
    skipped: int = 0


@dataclass
class DependencyResult:
    modified: int = 0
    skipped: int = 0


# ------------------------------------------------------------------
# Pinyin mapping (truncated for brevity; full map loaded from file or kept inline)
# ------------------------------------------------------------------
_PINYIN: dict[str, str] = {
    "一": "yi", "二": "er", "三": "san", "四": "si", "五": "wu",
    "六": "liu", "七": "qi", "八": "ba", "九": "jiu", "十": "shi",
    "百": "bai", "千": "qian", "万": "wan", "亿": "yi",
    "执": "zhi", "行": "xing", "摘": "zhai", "要": "yao", "背": "bei",
    "景": "jing", "问": "wen", "题": "ti", "功": "gong", "能": "neng",
    "范": "fan", "围": "wei", "非": "fei", "需": "xu", "求": "qiu",
    "用": "yong", "户": "hu", "画": "hua", "像": "xiang", "系": "xi",
    "统": "tong", "架": "jia", "构": "gou", "数": "shu", "据": "ju",
    "流": "liu", "运": "yun", "时": "shi", "为": "wei", "质": "zhi",
    "量": "liang", "属": "shu", "性": "xing", "维": "wei", "治": "zhi",
    "理": "li", "设": "she", "计": "ji", "总": "zong", "览": "lan",
    "列": "lie", "表": "biao", "详": "xiang", "情": "qing", "模": "mo",
    "块": "kuai", "组": "zu", "件": "jian", "接": "jie", "口": "kou",
    "契": "qi", "约": "yue", "库": "ku", "索": "suo", "引": "yin",
    "迁": "qian", "移": "yi", "划": "hua", "验": "yan", "收": "shou",
    "标": "biao", "准": "zhun", "测": "ce", "试": "shi", "报": "bao",
    "告": "gao", "风": "feng", "险": "xian", "管": "guan", "变": "bian",
    "更": "geng", "日": "ri", "志": "zhi", "审": "shen", "查": "cha",
    "记": "ji", "录": "lu", "决": "jue", "策": "ce", "冻": "dong",
    "结": "jie", "人": "ren", "工": "gong", "闸": "zha", "门": "men",
    "进": "jin", "度": "du", "追": "zhui", "踪": "zong", "状": "zhuang",
    "态": "tai", "机": "ji", "转": "zhuan", "换": "huan", "业": "ye",
    "务": "wu", "规": "gui", "则": "ze", "实": "shi", "体": "ti",
    "关": "guan", "领": "ling", "域": "yu", "型": "xing",
    "容": "rong", "器": "qi", "部": "bu", "署": "shu", "安": "an",
    "全": "quan", "监": "jian", "控": "kong", "异": "yi", "常": "chang",
    "处": "chu", "配": "pei", "置": "zhi",
    "权": "quan", "限": "xian", "角": "jiao", "色": "se", "登": "deng", "注": "zhu", "册": "ce", "退": "tui", "出": "chu",
    "首": "shou", "页": "ye", "仪": "yi", "盘": "pan", "看": "kan",
    "板": "ban", "导": "dao", "航": "hang", "菜": "cai", "单": "dan",
    "搜": "sou", "筛": "shai", "选": "xuan", "排": "pai", "序": "xu",
    "分": "fen", "弹": "tan", "窗": "chuang", "向": "xiang",
    "精": "jing", "灵": "ling", "帮": "bang", "助": "zhu", "文": "wen",
    "档": "dang", "反": "fan", "馈": "kui", "意": "yi", "见": "jian", "于": "yu", "版": "ban", "本": "ben", "新": "xin",
    "检": "jian", "同": "tong", "步": "bu", "备": "bei",
    "份": "fen", "恢": "hui", "复": "fu", "入": "ru", "打": "da",
    "印": "yin", "享": "xiang", "下": "xia", "载": "zai", "上": "shang",
    "传": "chuan", "拖": "tuo", "拽": "zhuai", "制": "zhi",
    "粘": "zhan", "贴": "tie", "剪": "jian", "切": "qie", "撤": "che",
    "销": "xiao", "重": "zhong", "做": "zuo", "取": "qu",
    "消": "xiao", "编": "bian", "辑": "ji", "删": "shan", "除": "chu",
    "建": "jian", "创": "chuang", "修": "xiu", "改": "gai",
    "阅": "yue", "读": "du", "预": "yu", "确": "que",
    "认": "ren", "提": "ti", "交": "jiao", "保": "bao", "存": "cun",
    "暂": "zan", "发": "fa", "布": "bu", "批": "pi",
    "通": "tong", "过": "guo", "驳": "bo", "回": "hui", "派": "pai",
    "指": "zhi", "督": "du", "询": "xun", "析": "xi",
    "图": "tu", "评": "ping", "估": "gu",
    "算": "suan", "警": "jing", "知": "zhi", "息": "xi", "邮": "you", "短": "duan",
    "信": "xin", "推": "tui", "送": "song", "订": "ding", "藏": "cang",
    "签": "qian", "类": "lei", "归": "gui", "目": "mu",
    "夹": "jia", "路": "lu", "径": "jing", "地": "di", "址": "zhi",
    "名": "ming", "称": "cheng", "识": "shi", "号": "hao", "代": "dai",
    "码": "ma", "期": "qi", "间": "jian", "长": "chang",
    "周": "zhou", "频": "pin", "率": "lv", "隔": "ge", "延": "yan",
    "迟": "chi", "等": "deng", "待": "dai", "超": "chao",
    "到": "dao", "截": "jie", "止": "zhi", "开": "kai", "始": "shi", "束": "shu", "启": "qi", "动": "dong", "停": "ting",
    "初": "chu", "化": "hua",
    "装": "zhuang", "卸": "xie", "线": "xian", "灰": "hui", "滚": "gun", "升": "sheng", "级": "ji",
    "降": "jiang", "兼": "jian", "适": "shi", "优": "you", "调": "tiao",
    "压": "ya", "缩": "suo", "缓": "huan", "加": "jia",
    "速": "su", "效": "xiao", "吞": "tun",
    "吐": "tu", "并": "bing", "负": "fu", "力": "li", "饱": "bao", "和": "he", "满": "man",
    "足": "zu", "达": "da", "完": "wan", "现": "xian", "付": "fu", "产": "chan", "生": "sheng", "绩": "ji",
    "水": "shui", "平": "ping", "潜": "qian", "毅": "yi", "专": "zhuan", "集": "ji", "中": "zhong", "洞": "dong", "造": "zao", "想": "xiang", "思": "si", "逻": "luo", "解": "jie", "忆": "yi", "学": "xue", "习": "xi",
    "应": "ying", "抗": "kang", "承": "cheng", "受": "shou",
    "忍": "ren", "包": "bao",
    "吸": "xi", "利": "li", "共": "gong", "覆": "fu", "盖": "gai", "核": "he", "心": "xin",
    # ---- Common particles ----
    "的": "de", "了": "le", "在": "zai", "是": "shi", "有": "you", "与": "yu", "及": "ji", "或": "huo", "但": "dan",
    "而": "er", "以": "yi", "将": "jiang", "把": "ba",
    "被": "bei", "让": "rang", "给": "gei", "对": "dui", "从": "cong", "由": "you", "自": "zi",
    "至": "zhi", "按": "an", "依": "yi", "照": "zhao",
    "因": "yin", "此": "ci", "故": "gu", "若": "ruo", "如": "ru",
    "即": "ji", "便": "bian", "虽": "sui", "然": "ran", "所": "suo",
    "之": "zhi", "其": "qi", "他": "ta", "它": "ta", "她": "ta",
    "们": "men", "哪": "na", "那": "na", "里": "li", "这": "zhe",
    "些": "xie", "什": "shen", "么": "me", "怎": "zen", "谁": "shui",
    "何": "he", "个": "ge", "还": "hai", "也": "ye",
    "都": "dou", "就": "jiu", "只": "zhi", "又": "you",
    "再": "zai", "最": "zui", "太": "tai", "很": "hen",
    "特": "te", "比": "bi", "较": "jiao", "相": "xiang", "当": "dang",
    "极": "ji", "尤": "you", "愈": "yu", "来": "lai", "越": "yue",
    "不": "bu", "没": "mei", "无": "wu", "未": "wei", "否": "fou",
    "勿": "wu", "莫": "mo", "毋": "wu",
}


def _pinyin(text: str) -> str:
    result = []
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            py = _PINYIN.get(ch)
            if py:
                result.append(py)
            else:
                result.append(f"u{ord(ch):04x}")
        else:
            result.append(ch)
    return "".join(result)


def slugify(text: str, max_len: int = 32) -> str:
    text = text.strip().lower()
    text = _pinyin(text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = text.strip("-")
    if not text:
        text = "section"
    return text[:max_len]


# ------------------------------------------------------------------
# Step 1 — Migrate legacy docs to baseline format
# ------------------------------------------------------------------
def migrate_legacy_docs(src_root: Path, dst_root: Path | None = None) -> MigrationResult:
    """Migrate legacy docs to DocForge standard format."""
    result = MigrationResult()
    iteration = "sdlc-visualizer"
    if dst_root is None:
        dst_root = src_root / "baseline"

    if not src_root.exists():
        result.errors.append(f"Source directory not found: {src_root}")
        return result

    md_files = sorted(src_root.rglob("*.md"))
    for src in md_files:
        if any(p in src.parts for p in ("baseline", "delta", "compiled", "_meta")):
            continue
        if src.name in (
            "progress.md", "plan.md", "tasks.md", "human-decisions.md",
            "master-flow.md", "prd-000-toc.md", "release-notes.md",
        ):
            result.skipped.append(str(src.relative_to(src_root)))
            continue
        try:
            content = src.read_text(encoding="utf-8-sig")
        except Exception as exc:
            result.errors.append(f"Read error {src}: {exc}")
            continue

        rel = src.relative_to(src_root)
        doc_type = "CHANGELOG"
        for part in rel.parts[:-1]:
            if part in DOC_TYPE_MAP:
                doc_type = DOC_TYPE_MAP[part]
                break
        if src.name in SPECIAL_FILES:
            doc_type, _ = SPECIAL_FILES[src.name]

        meta = _extract_meta(content, rel)
        seq = _derive_seq(src)
        prefix = doc_type.lower().replace("_", "-")
        module_hint = ""
        if "feature-" in str(rel):
            m = re.search(r"feature-(\d+)-([^/\\]+)", str(rel))
            if m:
                module_hint = f"-feat{m.group(1)}"
        elif "shared" in str(rel):
            module_hint = "-shared"
        fragment_id = f"{prefix}-{iteration}{module_hint}-{seq:03d}"

        body = _strip_legacy_meta(content)
        body = _inject_anchors(body)
        tags = [iteration]
        if doc_type in ("PRD", "ARCH", "DETAIL_DESIGN", "API_DESIGN", "DB_DESIGN"):
            tags.append("architecture")

        front = _build_front_matter(
            doc_type=doc_type,
            fragment_id=fragment_id,
            title=meta["title"] or src.stem,
            version=meta["version"],
            status=meta["status"],
            author=meta["author"],
            iteration=iteration,
            tags=tags,
        )
        new_content = f"{front}\n\n{body}\n"
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(new_content, encoding="utf-8")
        result.migrated.append((str(rel), fragment_id))

    # Manifest
    manifest_lines = [
        f"# Migration manifest for {iteration}",
        "",
        f"Migrated: {len(result.migrated)} files",
        f"Skipped: {len(result.skipped)} files",
        "",
        "## Migrated files",
        "",
    ]
    for rel, fid in result.migrated:
        manifest_lines.append(f"- `{rel}` → `{fid}`")
    if result.skipped:
        manifest_lines.extend(["", "## Skipped files", ""])
        for s in result.skipped:
            manifest_lines.append(f"- `{s}`")
    (dst_root / "_migration-manifest.md").write_text(
        "\n".join(manifest_lines) + "\n", encoding="utf-8"
    )
    return result


def _extract_meta(content: str, rel_path: Path) -> dict:
    meta = {"title": "", "version": "1.0.0", "status": "DRAFT", "author": "agent-migration", "date": "2026-06-10"}
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if m:
        meta["title"] = m.group(1).strip()
    m = re.search(r"[>\*]*\s*版本[：:]\s*([^\n\|]+)", content)
    if m:
        v = re.sub(r"^(PRD-000|HLD-001|DR-001)\s*", "", m.group(1).strip())
        v = v.replace("v", "").replace(" ", "")
        if re.match(r"^\d+\.\d+", v):
            meta["version"] = v
    m = re.search(r"[>\*]*\s*状态[：:]\s*\*?\*?([^\n\*]+)\*?\*?", content)
    if m:
        st = m.group(1).strip().lower()
        if "frozen" in st or "冻结" in st or "已通过" in st:
            meta["status"] = "FROZEN"
        elif "draft" in st or "草稿" in st:
            meta["status"] = "DRAFT"
        elif "review" in st or "评审" in st:
            meta["status"] = "REVIEW"
    m = re.search(r"[>\*]*\s*作者[：:]\s*([^\n]+)", content)
    if m:
        author = m.group(1).strip()
        if "AI" in author or "Agent" in author:
            meta["author"] = "agent-pm"
        elif "architect" in author.lower():
            meta["author"] = "agent-architect"
        elif "developer" in author.lower():
            meta["author"] = "agent-developer"
    m = re.search(r"[>\*]*\s*(?:日期|冻结时间|设计日期)[：:]\s*([^\n]+)", content)
    if m:
        meta["date"] = m.group(1).strip()
    return meta


def _strip_legacy_meta(content: str) -> str:
    lines = content.splitlines()
    result: list[str] = []
    changelog_stripped = False
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not result and line.startswith(">"):
            i += 1
            continue
        if not result and line.strip() == "":
            i += 1
            continue
        if not changelog_stripped and (
            "修改记录" in line or "版本历史" in line
            or ("版本" in line and "日期" in line and "修改人" in line)
        ):
            j = i
            while j < n and (lines[j].strip() == "" or lines[j].startswith("|") or lines[j].startswith(">")):
                j += 1
            i = j
            changelog_stripped = True
            continue
        if line.startswith(">"):
            j = i
            while j < n and lines[j].startswith(">"):
                j += 1
            block_text = "\n".join(lines[i:j])
            keywords = ["版本", "状态", "作者", "日期", "评审人", "冻结时间", "变更", "设计日期",
                        "模块编号", "模块名称", "关联需求", "关联用户故事", "上游基线", "下游基线"]
            if any(kw in block_text for kw in keywords):
                while j < n and lines[j].strip() == "":
                    j += 1
                i = j
                continue
        result.append(line)
        i += 1
    return "\n".join(result)


def _inject_anchors(content: str) -> str:
    seen: set[str] = set()

    def repl(m: re.Match) -> str:
        prefix = m.group(1)
        title = m.group(2).strip()
        existing = m.group(3)
        if existing:
            return m.group(0)
        slug = slugify(title)
        orig = slug
        counter = 1
        while slug in seen:
            slug = f"{orig}_{counter}"
            counter += 1
        seen.add(slug)
        return f"{prefix} {title} {{#sec-{slug}}}"

    pattern = re.compile(r"^(#{2,3})\s+(.+?)(\s*\{#[^}]+\})?\s*$", re.MULTILINE)
    return pattern.sub(repl, content)


def _build_front_matter(
    doc_type: str, fragment_id: str, title: str, version: str,
    status: str, author: str, iteration: str, tags: list[str],
) -> str:
    level = DOC_TYPE_LEVEL_MAP.get(doc_type, "")
    safe_title = title.replace('"', '\\"')
    lines = [
        "---",
        f'doc_type: "{doc_type}"',
        f'fragment_id: "{fragment_id}"',
        f'title: "{safe_title}"',
        f'version: "{version}"',
        'version_type: "BASELINE"',
        f'author: "{author}"',
        f'tags: {tags}',
        f'status: "{status}"',
        f'iteration: "{iteration}"',
        "dependencies:",
        "  - fragment_id: \"\"",
        "    version: \"\"",
    ]
    if level:
        lines.append("c4_binding:")
        lines.append(f'  level: "{level}"')
    lines.append("---")
    return "\n".join(lines)


def _derive_seq(src: Path) -> int:
    name = src.stem
    m = re.match(r"^(\d+)[-_]", name)
    if m:
        return int(m.group(1))
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    return (h % 900) + 1


# ------------------------------------------------------------------
# Step 2 — Extract C4 entities
# ------------------------------------------------------------------
def extract_c4_entities(src_root: Path, registry_path: Path) -> C4RegistryResult:
    systems: dict[str, dict] = {}
    actors: dict[str, dict] = {}
    containers: dict[str, dict] = {}
    components: dict[str, dict] = {}
    interfaces: list[dict] = []

    hld_dir = src_root / "high-level-design"
    for md_file in sorted(hld_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8-sig")
        if "Context" in content:
            l1 = [
                ("sdlc-visualizer", "SDLC Visualizer", ["Arsitect 可视化驾驶舱", "Pg_Viz"]),
                ("kimi-cli", "Kimi CLI", ["AI Skill 执行器", "Pg_Kimi"]),
                ("openui-service", "OpenUI Service", ["OpenUI Docker", "Pg_OpenUI"]),
                ("git", "Git", ["产物版本管理", "Pg_Git"]),
                ("local-filesystem", "本地文件系统", ["openspec/changes/", "Pg_FS"]),
            ]
            for eid, name, aliases in l1:
                if eid not in systems:
                    systems[eid] = {"name": name, "aliases": aliases, "level": "L1"}
            actors["developer"] = {"name": "超级个体", "aliases": ["独立开发者", "Tech Lead", "Pg_User"], "level": "L1"}
        if "Container" in content:
            l2 = [
                ("frontend-spa", "React 19 SPA", ["Frontend", "前端", "Pg_SPA", "SPA"]),
                ("backend-api", "FastAPI", ["REST API", "REST API + SSE", "Pg_API"]),
                ("skill-orchestrator", "Skill Orchestrator", ["PocketFlow 三阶段调度", "编排引擎", "Pg_Orchestrator"]),
                ("c4-dsl-engine", "C4 DSL Engine", ["自研解析渲染", "Pg_C4Engine"]),
                ("wireframe-engine", "WireframeEngine", ["领域感知线框", "Pg_Wireframe"]),
                ("sqlite-db", "SQLite", ["元数据与状态", "Pg_SQLite"]),
                ("git-repo", "Git 仓库", ["每项目独立 .git", "Pg_GitLocal"]),
                ("artifact-store", "产物目录", ["openspec/changes/", "Pg_Artifacts"]),
                ("kimi-cli-process", "Kimi CLI", ["子进程 STDIO", "Pg_KimiCLI"]),
                ("openui-docker", "OpenUI Docker", ["HTTP :7878", "Pg_OpenUI_Docker"]),
            ]
            for eid, name, aliases in l2:
                if eid not in containers:
                    containers[eid] = {"name": name, "aliases": aliases, "level": "L2"}
        if "Component" in content:
            l3 = [
                ("project-api", "Project API", ["项目 / 应用 / 模块 CRUD", "Pg_ProjectAPI"]),
                ("canvas-api", "Canvas API", ["节点 / 边 / 布局", "Pg_CanvasAPI"]),
                ("skill-api", "Skill API", ["导入 / 解析 / 执行", "Pg_SkillAPI"]),
                ("artifact-api", "Artifact API", ["产物 / 版本 / diff", "Pg_ArtifactAPI"]),
                ("gate-api", "Gate API", ["审批 / 摘要 / 历史", "Pg_GateAPI"]),
                ("c4-api", "C4 API", ["DSL / 渲染 / 导出", "Pg_C4API"]),
                ("prototype-api", "Prototype API", ["OpenUI / Wireframe", "Pg_ProtoAPI"]),
                ("project-service", "Project Service", ["双态管理 / Timebox", "Pg_ProjectSvc"]),
                ("orchestrator-service", "Orchestrator Service", ["DAG 调度 / 并行执行", "Pg_OrcheSvc"]),
                ("skill-service", "Skill Service", ["CLI 适配 / 日志捕获", "Pg_SkillSvc"]),
                ("artifact-service", "Artifact Service", ["Git 快照 / 冲突检测", "Pg_ArtifactSvc"]),
                ("gate-service", "Gate Service", ["自检摘要 / HITL", "Pg_GateSvc"]),
                ("size-estimate-service", "SizeEstimate Service", ["五维度评估 / 路由", "Pg_SizeSvc"]),
                ("c4-service", "C4 Service", ["DSL 生成 / 层级穿透", "Pg_C4Svc"]),
                ("prototype-service", "Prototype Service", ["OpenUI 适配 / Wireframe", "Pg_ProtoSvc"]),
                ("db-repository", "Repository", ["SQLAlchemy 2.0", "Pg_DBRepo"]),
                ("file-repository", "File Repository", ["本地文件系统", "Pg_FileRepo"]),
                ("git-repository", "Git Repository", ["GitPython", "Pg_GitRepo"]),
                ("cli-adapter", "CLI Adapter", ["Kimi STDIO", "Pg_CLIAdapter"]),
                ("sse-manager", "SSE Manager", ["事件推送", "Pg_SSEMgr"]),
            ]
            for eid, name, aliases in l3:
                if eid not in components:
                    components[eid] = {"name": name, "aliases": aliases, "level": "L3"}

    dd_dir = src_root / "detailed-design"
    for md_file in sorted(dd_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8-sig")
        for cls in _extract_python_classes(content):
            eid = _slug_id(cls)
            if eid not in components:
                components[eid] = {"name": cls, "aliases": [cls], "level": "L3"}
        for comp in _extract_react_components(content):
            eid = _slug_id(comp)
            if eid not in components:
                components[eid] = {"name": comp, "aliases": [comp], "level": "L3"}
        for node_id, label, _ in _extract_mermaid_nodes(content):
            suffixes = ["Router", "Service", "Repository", "Store", "Manager", "Engine", "Adapter", "Handler", "Controller"]
            if any(suffix in label for suffix in suffixes):
                first_word = label.split()[0] if " " in label else label
                generic = {"API", "Service", "Repository", "Store", "Manager", "Engine", "Handler", "Controller", "Router", "Adapter", "File", "Git", "DB", "SSE", "CLI"}
                if first_word in generic and len(label) < 10:
                    continue
                eid = _slug_id(first_word)
                if eid not in components:
                    components[eid] = {"name": label, "aliases": [node_id, label], "level": "L3"}

    ic_dir = src_root / "interface-contracts"
    for md_file in sorted(ic_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8-sig")
        for method, path in _extract_api_endpoints(content):
            iid = _slug_id(f"{method}-{path.replace('/', '-').replace('{', '').replace('}', '')}")
            interfaces.append({"id": iid, "method": method, "path": path})

    for md_file in sorted(dd_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8-sig")
        for method, path in _extract_api_endpoints(content):
            if not any(i["method"] == method and i["path"] == path for i in interfaces):
                iid = _slug_id(f"{method}-{path.replace('/', '-').replace('{', '').replace('}', '')}")
                interfaces.append({"id": iid, "method": method, "path": path})

    # ------------------------------------------------------------------
    # Extract relationships and component container assignments from
    # Mermaid diagrams in all design documents.
    # ------------------------------------------------------------------
    relationships: list[dict] = []
    all_design_dirs = [hld_dir, dd_dir, src_root / "interface-contracts"]

    for design_dir in all_design_dirs:
        if not design_dir.exists():
            continue
        for md_file in sorted(design_dir.rglob("*.md")):
            content = md_file.read_text(encoding="utf-8-sig")
            mermaid_rels, mermaid_membership = _extract_mermaid_data(content)

            all_elements = {**systems, **actors, **containers, **components}
            for src, dst, desc in mermaid_rels:
                src_id = _map_mermaid_id(src, all_elements)
                dst_id = _map_mermaid_id(dst, all_elements)
                if src_id and dst_id:
                    rel = {"source": src_id, "target": dst_id, "description": desc}
                    if rel not in relationships:
                        relationships.append(rel)

            # Map subgraph-based container assignments for components
            for mermaid_node, _subgraph_name in mermaid_membership.items():
                comp_id = _map_mermaid_id(mermaid_node, components)
                if not comp_id:
                    continue
                # Subgraph names in L3 diagrams are layers (API/Domain/Infra),
                # not container names.  We map via the hard-coded table first,
                # and only fall back to subgraph-derived info when useful.
                if comp_id not in _COMPONENT_CONTAINER_MAP:
                    # If the diagram is clearly a backend diagram,
                    # mark as backend-api unless already inferred otherwise.
                    pass

    # Apply container_id to all components
    for comp_id, comp_info in components.items():
        if "container_id" not in comp_info:
            comp_info["container_id"] = _infer_component_container(
                comp_id, comp_info.get("name", "")
            )

    registry = {
        "systems": systems,
        "actors": actors,
        "containers": containers,
        "components": components,
        "interfaces": interfaces,
        "relationships": relationships,
    }
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_path.open("w", encoding="utf-8") as f:
        yaml.dump(registry, f, allow_unicode=True, sort_keys=False, width=120)
    return C4RegistryResult(
        systems=len(systems),
        actors=len(actors),
        containers=len(containers),
        components=len(components),
        interfaces=len(interfaces),
        registry_path=str(registry_path),
    )


def _slug_id(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[\ud800-\udfff]", "", text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = text.strip("-")
    return text


def _clean_mermaid_label(label: str) -> str:
    label = re.sub(r"<[^>]+>", " ", label)
    label = re.sub(r"[\ud800-\udfff]", "", label)
    label = label.split("\n")[0].split("/")[0].strip()
    return label


def _extract_mermaid_nodes(content: str) -> list[tuple[str, str, str]]:
    entities: list[tuple[str, str, str]] = []
    for mermaid_match in re.finditer(r"```mermaid\n(.*?)```", content, re.DOTALL):
        diagram = mermaid_match.group(1)
        diagram_type = "flowchart"
        first_line = diagram.strip().splitlines()[0] if diagram.strip() else ""
        if "erDiagram" in first_line:
            diagram_type = "er"
        elif "flowchart" in first_line or "graph" in first_line:
            diagram_type = "flowchart"
        if diagram_type == "flowchart":
            for m in re.finditer(r"([A-Za-z_]\w*)\s*\[\"([^\"]+)\"\]", diagram):
                node_id = m.group(1)
                label = _clean_mermaid_label(m.group(2))
                if node_id.startswith("subgraph") or label in (
                    "API", "Service", "Repository", "Store", "Manager",
                    "Engine", "Handler", "Controller", "Router", "Adapter",
                    "API 层", "Service 层", "Repository 层",
                ):
                    continue
                if len(label) < 3:
                    continue
                entities.append((node_id, label, "flowchart"))
    return entities


def _extract_mermaid_data(content: str) -> tuple[list[tuple[str, str, str]], dict[str, str]]:
    """Extract relationships and subgraph memberships from Mermaid diagrams.

    Returns:
        relationships: list of (source_mermaid_id, target_mermaid_id, description)
        memberships: dict mapping node_mermaid_id -> subgraph_name
    """
    relationships: list[tuple[str, str, str]] = []
    memberships: dict[str, str] = {}

    for mermaid_match in re.finditer(r"```mermaid\n(.*?)```", content, re.DOTALL):
        diagram = mermaid_match.group(1)
        lines = diagram.splitlines()

        current_subgraph: str | None = None
        subgraph_depth = 0

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("%%"):
                continue

            # Skip style / classDef / linkStyle / direction / click lines
            if line.startswith(("style ", "classDef ", "linkStyle ", "direction ", "click ")):
                continue

            # Subgraph start: subgraph name["label"] or subgraph name
            if line.startswith("subgraph "):
                m = re.match(r'subgraph\s+([A-Za-z_]\w*)(?:\[[^\]]*\]|\([^\)]*\)|\{[^}]*\})?', line)
                if m:
                    current_subgraph = m.group(1)
                    subgraph_depth += 1
                continue

            # Subgraph end
            if line == "end":
                if subgraph_depth > 0:
                    subgraph_depth -= 1
                    if subgraph_depth == 0:
                        current_subgraph = None
                continue

            # Relationship: A --> B  or  A -->|desc| B  or  A --- B
            rel_m = re.match(
                r'^([A-Za-z_]\w*)\s+(-->|---|==>|===>|-\.->)\s*(?:\|([^|]*)\|)?\s+([A-Za-z_]\w*)',
                line,
            )
            if rel_m:
                src, dst, desc = rel_m.group(1), rel_m.group(4), (rel_m.group(3) or "")
                desc = desc.replace("<br/>", " ").replace("<br>", " ").strip()
                relationships.append((src, dst, desc))
                continue

            # Node declaration inside subgraph: nodeId["label"] / nodeId((...)) / nodeId{...}
            node_m = re.match(r'^([A-Za-z_]\w*)(?:\[[^\]]*\]|\([^\)]*\)|\{[^}]*\])', line)
            if node_m and current_subgraph:
                node_id = node_m.group(1)
                if node_id not in memberships:
                    memberships[node_id] = current_subgraph

    return relationships, memberships


def _map_mermaid_id(mermaid_id: str, elements: dict[str, dict]) -> str | None:
    """Map a Mermaid node ID (e.g. Pg_SPA) to a registry element ID (e.g. frontend-spa)."""
    if mermaid_id in elements:
        return mermaid_id
    for eid, info in elements.items():
        aliases = info.get("aliases", [])
        if mermaid_id in aliases:
            return eid
    return None


# Component → Container heuristic mapping (for HLD L3 components)
_COMPONENT_CONTAINER_MAP: dict[str, str] = {
    "c4-api": "c4-dsl-engine",
    "c4-service": "c4-dsl-engine",
    "prototype-api": "wireframe-engine",
    "prototype-service": "wireframe-engine",
    "orchestrator-service": "skill-orchestrator",
    "cli-adapter": "skill-orchestrator",
}


def _infer_component_container(comp_id: str, comp_name: str) -> str:
    """Infer which container a component belongs to."""
    if comp_id in _COMPONENT_CONTAINER_MAP:
        return _COMPONENT_CONTAINER_MAP[comp_id]
    # React components (PascalCase names) usually belong to frontend
    if comp_name and comp_name[0].isupper() and any(
        suffix in comp_name for suffix in
        ["Page", "Panel", "Shell", "Handle", "Layer", "Bar", "Card",
         "List", "Modal", "Dialog", "Drawer", "Tab", "View", "Manager"]
    ):
        return "frontend-spa"
    # Default backend container
    return "backend-api"


def _extract_python_classes(content: str) -> list[str]:
    classes: list[str] = []
    pattern = r"class\s+([A-Z]\w*(?:Service|Repository|Router|Store|Manager|Engine|Adapter|Handler|Controller|DTO|Schema|Model))"
    for m in re.finditer(pattern, content):
        name = m.group(1)
        if name not in classes:
            classes.append(name)
    return classes


def _extract_react_components(content: str) -> list[str]:
    comps: list[str] = []
    pattern1 = r"`([A-Z][a-zA-Z]+(?:Tab|Panel|Shell|Handle|Layer|Controller|Bar|Manager|Router|Store|Pane|View|Card|List|Grid|Form|Modal|Dialog|Drawer|Badge|Popover|Sidebar|Mask|Confirmation))`"
    for m in re.finditer(pattern1, content):
        name = m.group(1)
        if name not in comps:
            comps.append(name)
    return comps


def _extract_api_endpoints(content: str) -> list[tuple[str, str]]:
    endpoints: list[tuple[str, str]] = []
    for m in re.finditer(r"`([A-Z]+)\s+(/[a-zA-Z0-9/{}._-]+)`", content):
        method, path = m.group(1), m.group(2)
        if (method, path) not in endpoints:
            endpoints.append((method, path))
    return endpoints


# ------------------------------------------------------------------
# Step 3 — Inject C4 tags
# ------------------------------------------------------------------
def inject_c4_tags(baseline_root: Path, registry_path: Path) -> C4TagResult:
    with registry_path.open("r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    modified = 0
    skipped = 0

    for md_file in sorted(baseline_root.rglob("*.md")):
        if md_file.name.startswith("_"):
            continue
        result = _inject_tags_for_doc(md_file, registry)
        if result is None:
            skipped += 1
            continue
        md_file.write_text(result, encoding="utf-8")
        modified += 1

    return C4TagResult(modified=modified, skipped=skipped)


def _inject_tags_for_doc(baseline_path: Path, registry: dict) -> str | None:
    content = baseline_path.read_text(encoding="utf-8-sig")
    meta, body = _parse_front_matter(content)
    if not meta:
        return None

    doc_type = meta.get("doc_type", "")
    level = meta.get("c4_binding", {}).get("level", "")
    if not level:
        level = {"PRD": "L1", "ARCH": "L2", "DB_DESIGN": "L2", "DETAIL_DESIGN": "L3", "API_DESIGN": "L3"}.get(doc_type, "")
    if not level:
        return None

    entities = _collect_matching_entities(registry, level)
    found_tags: list[str] = []
    for tag, names in entities:
        if _body_contains_any(body, names):
            found_tags.append(tag)

    if not found_tags:
        return None
    if "> **C4 绑定引用**：" in content:
        return None

    block_lines = ["> **C4 绑定引用**："]
    for tag in sorted(set(found_tags)):
        block_lines.append(f"> - `{tag}`")
    block = "\n".join(block_lines)

    lines = body.splitlines()
    heading_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("# "):
            heading_idx = i
            break

    if heading_idx == -1:
        new_body = block + "\n\n" + body
    else:
        insert_idx = heading_idx + 1
        while insert_idx < len(lines) and lines[insert_idx].strip() == "":
            insert_idx += 1
        lines.insert(insert_idx, "")
        lines.insert(insert_idx + 1, block)
        lines.insert(insert_idx + 2, "")
        new_body = "\n".join(lines)

    new_content = f"---\n{yaml.dump(meta, allow_unicode=True, sort_keys=False, width=120).rstrip()}\n---\n\n{new_body}\n"
    return new_content


def _parse_front_matter(content: str) -> tuple[dict, str]:
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    fm = yaml.safe_load(content[4:end])
    body = content[end + 5:].lstrip("\n")
    return fm or {}, body


def _body_contains_any(body: str, names: list[str]) -> bool:
    clean = re.sub(r"```mermaid\n.*?```", "", body, flags=re.DOTALL)
    return any(name in clean for name in names)


def _collect_matching_entities(registry: dict, doc_level: str) -> list[tuple[str, list[str]]]:
    tags: list[tuple[str, list[str]]] = []
    if doc_level == "L1":
        for eid, info in registry.get("systems", {}).items():
            tags.append((f"@C4-L1-System:{eid}", [info["name"]] + info.get("aliases", [])))
        for eid, info in registry.get("actors", {}).items():
            tags.append((f"@C4-L1-Actor:{eid}", [info["name"]] + info.get("aliases", [])))
    elif doc_level == "L2":
        for eid, info in registry.get("containers", {}).items():
            tags.append((f"@C4-L2-Container:{eid}", [info["name"]] + info.get("aliases", [])))
        for eid, info in registry.get("systems", {}).items():
            tags.append((f"@C4-L1-System:{eid}", [info["name"]] + info.get("aliases", [])))
    elif doc_level == "L3":
        for eid, info in registry.get("components", {}).items():
            if eid in _GENERIC_IDS:
                continue
            tags.append((f"@C4-L3-Component:{eid}", [info["name"]] + info.get("aliases", [])))
        for iface in registry.get("interfaces", []):
            tags.append((f"@C4-Interface:{iface['method']} {iface['path']}", [f"{iface['method']} {iface['path']}", iface["path"]]))
        for eid, info in registry.get("containers", {}).items():
            tags.append((f"@C4-L2-Container:{eid}", [info["name"]] + info.get("aliases", [])))
        for eid, info in registry.get("systems", {}).items():
            tags.append((f"@C4-L1-System:{eid}", [info["name"]] + info.get("aliases", [])))
    return tags


# ------------------------------------------------------------------
# Step 4 — Fill dependencies
# ------------------------------------------------------------------
def fill_dependencies(baseline_root: Path) -> DependencyResult:
    index = _build_index(baseline_root)
    alias_map = _build_alias_map(index)
    alias_map["API-SPEC"] = "api-design-sdlc-visualizer-shared-824"
    alias_map["DB-SCHEMA"] = "db-design-sdlc-visualizer-shared-607"

    modified = 0
    skipped = 0

    for f in sorted(baseline_root.rglob("*.md")):
        if f.name.startswith("_"):
            continue
        content = f.read_text(encoding="utf-8-sig")
        m = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
        if not m:
            skipped += 1
            continue

        meta = yaml.safe_load(m.group(1))
        body = content[m.end():]

        fid = meta.get("fragment_id")
        doc_type = meta.get("doc_type", "")
        feature = index.get(fid, {}).get("feature")

        dep_ids: set[str] = set()

        for dep_fid in _get_default_upstream(doc_type, feature, fid, index):
            if dep_fid in index and dep_fid != fid:
                dep_ids.add(dep_fid)

        if fid not in ("prd-sdlc-visualizer-000", "arch-sdlc-visualizer-000"):
            refs = _extract_refs_from_body(body)
            for ref in refs:
                resolved = _resolve_alias(ref, alias_map, doc_type)
                if resolved and resolved in index and resolved != fid:
                    dep_ids.add(resolved)

        if doc_type == "DETAIL_DESIGN" and feature and fid != "arch-sdlc-visualizer-000":
            for other_fid, other_info in index.items():
                if other_fid == fid:
                    continue
                other_feat = other_info.get("feature")
                if not other_feat:
                    continue
                num = other_feat.replace("feature-", "")
                dr_pattern = f"DR-{int(num):03d}"
                if dr_pattern in body and other_fid in index:
                    dep_ids.add(other_fid)

        if not dep_ids:
            skipped += 1
            continue

        deps_list: list[dict] = []
        for dep_fid in sorted(dep_ids):
            dep_version = index.get(dep_fid, {}).get("version", "1.0.0")
            deps_list.append({"fragment_id": dep_fid, "version": dep_version})

        meta["dependencies"] = deps_list
        new_fm = yaml.dump(meta, allow_unicode=True, sort_keys=False, width=120).rstrip()
        new_content = f"---\n{new_fm}\n---{body}"
        f.write_text(new_content, encoding="utf-8")
        modified += 1

    return DependencyResult(modified=modified, skipped=skipped)


def _build_index(baseline_root: Path) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for f in sorted(baseline_root.rglob("*.md")):
        if f.name.startswith("_"):
            continue
        content = f.read_text(encoding="utf-8-sig")
        m = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
        if not m:
            continue
        meta = yaml.safe_load(m.group(1))
        if not meta:
            continue
        fid = meta.get("fragment_id")
        if not fid:
            continue
        p = str(f.relative_to(baseline_root)).replace("\\", "/")
        feat = None
        m2 = re.search(r"feature-(\d+)-([^/]+)", p)
        if m2:
            feat = f"feature-{m2.group(1)}"
        index[fid] = {
            "path": p,
            "version": meta.get("version", "1.0.0"),
            "doc_type": meta.get("doc_type", ""),
            "feature": feat,
        }
    return index


def _build_alias_map(index: dict) -> dict[str, str | list[str]]:
    alias_map: dict[str, str | list[str]] = {
        "PRD-000": "prd-sdlc-visualizer-000",
        "HLD-001": "arch-sdlc-visualizer-001",
        "HLD-002": "arch-sdlc-visualizer-002",
        "HLD-003": "arch-sdlc-visualizer-003",
        "HLD-004": "arch-sdlc-visualizer-004",
        "HLD-005": "arch-sdlc-visualizer-005",
    }
    for fid, info in index.items():
        feat = info.get("feature")
        if not feat:
            continue
        num = feat.replace("feature-", "")
        dr_key = f"DR-{int(num):03d}"
        if dr_key not in alias_map:
            alias_map[dr_key] = []
        if isinstance(alias_map[dr_key], list):
            alias_map[dr_key].append(fid)
    return alias_map


def _resolve_alias(alias: str, alias_map: dict, current_doc_type: str) -> str | None:
    val = alias_map.get(alias)
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if current_doc_type == "DETAIL_DESIGN":
        for v in val:
            if "detail-design" in v:
                return v
    elif current_doc_type == "PRD":
        for v in val:
            if "prd-" in v and "feat" in v:
                return v
    return val[0] if val else None


def _extract_refs_from_body(body: str) -> set[str]:
    refs: set[str] = set()
    for m in re.finditer(r"\b(PRD-000|HLD-00[0-5]|DR-0\d{2})\b", body):
        refs.add(m.group(1))
    for m in re.finditer(r"\bGate\s+(1|2|2\.5|3)\b", body):
        gate = m.group(1)
        if gate == "1":
            refs.add("PRD-000")
        elif gate == "2":
            refs.add("HLD-001")
        elif gate == "2.5":
            refs.add("DR-001")
    for m in re.finditer(r"\.\./[^)\s\]]+\.md", body):
        path = m.group(0)
        stem = Path(path).stem
        if "requirements-overview" in stem:
            refs.add("PRD-000")
        elif "architecture-core" in stem:
            refs.add("HLD-001")
        elif "data-flow" in stem:
            refs.add("HLD-002")
        elif "runtime-behavior" in stem:
            refs.add("HLD-003")
        elif "api-spec" in stem:
            refs.add("API-SPEC")
        elif "db-schema" in stem:
            refs.add("DB-SCHEMA")
    return refs


def _get_default_upstream(doc_type: str, feature: str | None, fid: str, index: dict) -> list[str]:
    deps: list[str] = []
    if fid == "prd-sdlc-visualizer-000":
        for bf_fid in ("changelog-sdlc-visualizer-146", "changelog-sdlc-visualizer-392"):
            if bf_fid in index:
                deps.append(bf_fid)
        return deps
    if fid == "arch-sdlc-visualizer-000":
        deps.append("prd-sdlc-visualizer-000")
        return deps
    if doc_type == "PRD" and feature:
        deps.append("prd-sdlc-visualizer-000")
        deps.append("arch-sdlc-visualizer-000")
    elif doc_type == "ARCH":
        deps.append("prd-sdlc-visualizer-000")
    elif doc_type == "DETAIL_DESIGN":
        if feature:
            num = feature.replace("feature-", "")
            req_fid = f"prd-sdlc-visualizer-feat{int(num):02d}-629"
            if req_fid in index:
                deps.append(req_fid)
        deps.extend(["arch-sdlc-visualizer-000", "arch-sdlc-visualizer-001"])
        if "api-design-sdlc-visualizer-shared-824" in index:
            deps.append("api-design-sdlc-visualizer-shared-824")
        if "db-design-sdlc-visualizer-shared-607" in index:
            deps.append("db-design-sdlc-visualizer-shared-607")
    elif doc_type == "API_DESIGN":
        deps.extend(["arch-sdlc-visualizer-001", "arch-sdlc-visualizer-002"])
        if "db-design-sdlc-visualizer-shared-607" in index:
            deps.append("db-design-sdlc-visualizer-shared-607")
    elif doc_type == "DB_DESIGN":
        deps.extend(["arch-sdlc-visualizer-002", "arch-sdlc-visualizer-001"])
    elif doc_type == "TEST_PLAN":
        deps.extend(["prd-sdlc-visualizer-000", "arch-sdlc-visualizer-000"])
    return deps
