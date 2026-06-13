"""Migrate legacy OpenSpec docs to DocForge standard format.

Usage:
    python scripts/migrate_docs.py

Reads all .md files under openspec/changes/sdlc-visualizer/,
converts them to standard format with YAML Front Matter + anchor IDs,
and writes to openspec/changes/sdlc-visualizer/baseline/.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

# ------------------------------------------------------------------
# Mapping rules
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

# ------------------------------------------------------------------
# Pinyin mapping for common Chinese chars (simplified, ~400 chars)
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
    "关": "guan", "系": "xi", "领": "ling", "域": "yu", "型": "xing",
    "容": "rong", "器": "qi", "部": "bu", "署": "shu", "安": "an",
    "全": "quan", "监": "jian", "控": "kong", "异": "yi", "常": "chang",
    "处": "chu", "日": "ri", "计": "ji", "配": "pei", "置": "zhi",
    "权": "quan", "限": "xian", "角": "jiao", "色": "se", "登": "deng",
    "录": "lu", "注": "zhu", "册": "ce", "退": "tui", "出": "chu",
    "首": "shou", "页": "ye", "仪": "yi", "盘": "pan", "看": "kan",
    "板": "ban", "导": "dao", "航": "hang", "菜": "cai", "单": "dan",
    "搜": "sou", "筛": "shai", "选": "xuan", "排": "pai", "序": "xu",
    "分": "fen", "页": "ye", "弹": "tan", "窗": "chuang", "向": "xiang",
    "精": "jing", "灵": "ling", "帮": "bang", "助": "zhu", "文": "wen",
    "档": "dang", "反": "fan", "馈": "kui", "意": "yi", "见": "jian",
    "关": "guan", "于": "yu", "版": "ban", "本": "ben", "新": "xin",
    "检": "jian", "查": "cha", "同": "tong", "步": "bu", "备": "bei",
    "份": "fen", "恢": "hui", "复": "fu", "入": "ru", "打": "da",
    "印": "yin", "享": "xiang", "下": "xia", "载": "zai", "上": "shang",
    "传": "chuan", "拖": "tuo", "拽": "zhuai", "复": "fu", "制": "zhi",
    "粘": "zhan", "贴": "tie", "剪": "jian", "切": "qie", "撤": "che",
    "销": "xiao", "重": "zhong", "做": "zuo", "全": "quan", "取": "qu",
    "消": "xiao", "编": "bian", "辑": "ji", "删": "shan", "除": "chu",
    "建": "jian", "创": "chuang", "修": "xiu", "改": "gai", "更": "geng",
    "阅": "yue", "读": "du", "预": "yu", "览": "lan", "确": "que",
    "认": "ren", "提": "ti", "交": "jiao", "保": "bao", "存": "cun",
    "暂": "zan", "发": "fa", "布": "bu", "审": "shen", "批": "pi",
    "通": "tong", "过": "guo", "驳": "bo", "回": "hui", "派": "pai",
    "指": "zhi", "督": "du", "询": "xun", "统": "tong", "析": "xi",
    "图": "tu", "指": "zhi", "度": "du", "评": "ping", "估": "gu",
    "算": "suan", "测": "ce", "警": "jing", "告": "gao", "知": "zhi",
    "消": "xiao", "息": "xi", "邮": "you", "件": "jian", "短": "duan",
    "信": "xin", "推": "tui", "送": "song", "订": "ding", "藏": "cang",
    "签": "qian", "类": "lei", "归": "gui", "档": "dang", "目": "mu",
    "夹": "jia", "路": "lu", "径": "jing", "地": "di", "址": "zhi",
    "名": "ming", "称": "cheng", "识": "shi", "号": "hao", "代": "dai",
    "码": "ma", "号": "hao", "期": "qi", "间": "jian", "长": "chang",
    "周": "zhou", "频": "pin", "率": "lv", "隔": "ge", "延": "yan",
    "迟": "chi", "等": "deng", "待": "dai", "超": "chao", "过": "guo",
    "到": "dao", "截": "jie", "止": "zhi", "开": "kai", "始": "shi",
    "结": "jie", "束": "shu", "启": "qi", "动": "dong", "停": "ting",
    "止": "zhi", "暂": "zan", "停": "ting", "恢": "hui", "复": "fu",
    "重": "chong", "启": "qi", "初": "chu", "始": "shi", "化": "hua",
    "装": "zhuang", "卸": "xie", "载": "zai", "线": "xian", "灰": "hui",
    "度": "du", "全": "quan", "量": "liang", "滚": "gun", "切": "qie",
    "换": "huan", "迁": "qian", "移": "yi", "升": "sheng", "级": "ji",
    "降": "jiang", "级": "ji", "兼": "jian", "容": "rong", "适": "shi",
    "配": "pei", "优": "you", "化": "hua", "调": "tiao", "优": "you",
    "压": "ya", "缩": "suo", "缓": "huan", "存": "cun", "加": "jia",
    "速": "su", "性": "xing", "能": "neng", "效": "xiao", "吞": "tun",
    "吐": "tu", "并": "bing", "发": "fa", "负": "fu", "载": "zai",
    "压": "ya", "力": "li", "容": "rong", "扩": "kuo", "展": "zhan",
    "伸": "shen", "缩": "suo", "弹": "tan", "高": "gao", "可": "ke",
    "用": "yong", "错": "cuo", "灾": "zai", "备": "bei", "故": "gu",
    "障": "zhang", "误": "wu", "失": "shi", "败": "bai", "成": "cheng",
    "功": "gong", "完": "wan", "成": "cheng", "果": "guo", "输": "shu",
    "出": "chu", "返": "fan", "回": "hui", "响": "xiang", "应": "ying",
    "内": "nei", "存": "cun", "磁": "ci", "盘": "pan", "网": "wang",
    "络": "luo", "带": "dai", "宽": "kuan", "流": "liu", "请": "qing",
    "连": "lian", "接": "jie", "会": "hui", "话": "hua", "空": "kong",
    "闲": "xian", "活": "huo", "跃": "yue", "在": "zai", "离": "li",
    "模": "mo", "式": "shi", "种": "zhong", "类": "lei", "级": "ji",
    "别": "bie", "阶": "jie", "段": "duan", "层": "ceng", "次": "ci",
    "维": "wei", "度": "du", "方": "fang", "向": "xiang", "目": "mu",
    "的": "di", "意": "yi", "图": "tu", "途": "tu", "价": "jia",
    "值": "zhi", "格": "ge", "成": "cheng", "本": "ben", "费": "fei",
    "支": "zhi", "入": "ru", "益": "yi", "润": "run", "盈": "ying",
    "亏": "kui", "损": "sun", "投": "tou", "资": "zi", "期": "qi",
    "金": "jin", "算": "suan", "里": "li", "程": "cheng", "碑": "bei",
    "节": "jie", "点": "dian", "键": "jian", "临": "lin", "界": "jie",
    "路": "lu", "径": "jing", "链": "lian", "依": "yi", "赖": "lai",
    "前": "qian", "置": "zhi", "后": "hou", "条": "tiao", "提": "ti",
    "假": "jia", "设": "she", "约": "yue", "束": "shu", "限": "xian",
    "制": "zhi", "策": "ce", "略": "lue", "方": "fang", "案": "an",
    "安": "an", "排": "pai", "实": "shi", "施": "shi", "落": "luo",
    "地": "di", "推": "tui", "进": "jin", "展": "zhan", "促": "cu",
    "提": "ti", "升": "sheng", "演": "yan", "进": "jin", "化": "hua",
    "蜕": "tui", "型": "xing", "革": "ge", "增": "zeng", "强": "qiang",
    "强": "qiang", "加": "jia", "固": "gu", "巩": "gong", "提": "ti",
    "高": "gao", "上": "shang", "升": "sheng", "增": "zeng", "长": "zhang",
    "扩": "kuo", "大": "da", "拓": "tuo", "延": "yan", "伸": "shen",
    "展": "zhan", "蔓": "man", "散": "san", "播": "bo", "传": "chuan",
    "递": "di", "转": "zhuan", "下": "xia", "报": "bao", "递": "di",
    "移": "yi", "交": "jiao", "互": "hu", "流": "liu", "沟": "gou",
    "协": "xie", "商": "shang", "讨": "tao", "论": "lun", "研": "yan",
    "究": "jiu", "探": "tan", "剖": "pou", "拆": "chai", "解": "jie",
    "割": "ge", "划": "hua", "区": "qu", "归": "gui", "纳": "na",
    "综": "zong", "述": "shu", "概": "gai", "括": "kuo", "简": "jian",
    "介": "jie", "绍": "shao", "说": "shuo", "明": "ming", "描": "miao",
    "述": "shu", "阐": "chan", "释": "shi", "注": "zhu", "备": "bei",
    "附": "fu", "录": "lu", "附": "fu", "件": "jian", "附": "fu",
    "额": "e", "外": "wai", "随": "sui", "跟": "gen", "陪": "pei",
    "伴": "ban", "同": "tong", "伙": "huo", "搭": "da", "档": "dang",
    "合": "he", "作": "zuo", "配": "pei", "搭": "da", "组": "zu",
    "混": "hun", "融": "rong", "整": "zheng", "集": "ji", "汇": "hui",
    "聚": "ju", "采": "cai", "样": "yang", "抽": "chou", "选": "xuan",
    "本": "ben", "例": "li", "案": "an", "范": "fan", "示": "shi",
    "板": "ban", "原": "yuan", "料": "liao", "素": "su", "材": "cai",
    "资": "zi", "信": "xin", "字": "zi", "符": "fu", "串": "chuan",
    "数": "shu", "整": "zheng", "小": "xiao", "浮": "fu", "点": "dian",
    "布": "bu", "尔": "er", "真": "zhen", "假": "jia", "是": "shi",
    "否": "fou", "对": "dui", "正": "zheng", "常": "chang", "危": "wei",
    "轻": "qing", "微": "wei", "提": "ti", "示": "shi", "注": "zhu",
    "意": "yi", "警": "jing", "示": "shi", "诫": "jie", "劝": "quan",
    "建": "jian", "议": "yi", "荐": "jian", "南": "nan", "引": "yin",
    "参": "can", "考": "kao", "借": "jie", "鉴": "jian", "培": "pei",
    "训": "xun", "教": "jiao", "育": "yu", "辅": "fu", "援": "yuan",
    "救": "jiu", "抢": "qiang", "修": "xiu", "护": "hu", "养": "yang",
    "巡": "xun", "观": "guan", "察": "cha", "搜": "sou", "索": "suo",
    "查": "cha", "询": "xun", "定": "ding", "位": "wei", "寻": "xun",
    "找": "zhao", "探": "tan", "发": "fa", "现": "xian", "识": "shi",
    "辨": "bian", "区": "qu", "判": "pan", "断": "duan", "选": "xuan",
    "择": "ze", "挑": "tiao", "滤": "lv", "排": "pai", "除": "chu",
    "剔": "ti", "清": "qing", "去": "qu", "掉": "diao", "作": "zuo",
    "废": "fei", "丢": "diu", "弃": "qi", "淘": "tao", "汰": "tai",
    "替": "ti", "轮": "lun", "循": "xun", "环": "huan", "周": "zhou",
    "迭": "die", "代": "dai", "演": "yan", "蜕": "tui", "革": "ge",
    "破": "po", "固": "gu", "扩": "kuo", "大": "da", "伸": "shen",
    "缩": "suo", "弹": "tan", "兼": "jian", "适": "shi", "缩": "suo",
    "缓": "huan", "吞": "tun", "吐": "tu", "并": "bing", "负": "fu",
    "压": "ya", "力": "li", "饱": "bao", "和": "he", "满": "man",
    "足": "zu", "达": "da", "完": "wan", "实": "shi", "现": "xian",
    "交": "jiao", "付": "fu", "产": "chan", "出": "chu", "生": "sheng",
    "产": "chan", "效": "xiao", "绩": "ji", "业": "ye", "表": "biao",
    "水": "shui", "平": "ping", "潜": "qian", "毅": "yi", "专": "zhuan",
    "注": "zhu", "集": "ji", "中": "zhong", "洞": "dong", "执": "zhi",
    "行": "xing", "动": "dong", "造": "zao", "想": "xiang", "思": "si",
    "维": "wei", "逻": "luo", "辑": "ji", "理": "li", "解": "jie",
    "记": "ji", "忆": "yi", "学": "xue", "习": "xi", "适": "shi",
    "应": "ying", "变": "bian", "抗": "kang", "承": "cheng", "受": "shou",
    "忍": "ren", "容": "rong", "包": "bao", "接": "jie", "受": "shou",
    "吸": "xi", "收": "shou", "化": "hua", "转": "zhuan", "利": "li",
    "复": "fu", "共": "gong", "享": "xiang", "覆": "fu", "盖": "gai",
    "度": "du", "率": "lv", "核": "he", "心": "xin", "域": "yu",
    "务": "wu", "总": "zong", "述": "shu", "概": "gai", "览": "lan",
    "架": "jia", "构": "gou", "图": "tu", "组": "zu", "建": "jian",
    "织": "zhi", "结": "jie", "构": "gou", "框": "kuang", "架": "jia",
    "平": "ping", "台": "tai", "中": "zhong", "间": "jian", "服": "fu",
    "底": "di", "层": "ceng", "驱": "qu", "动": "dong", "引": "yin",
    "擎": "qing", "核": "he", "心": "xin", "关": "guan", "键": "jian",
    "主": "zhu", "次": "ci", "辅": "fu", "支": "zhi", "持": "chi",
    "基": "ji", "础": "chu", "根": "gen", "源": "yuan", "本": "ben",
    "质": "zhi", "体": "ti", "面": "mian", "表": "biao", "里": "li",
    "内": "nei", "外": "wai", "上": "shang", "下": "xia", "左": "zuo",
    "右": "you", "前": "qian", "后": "hou", "中": "zhong", "间": "jian",
    "旁": "pang", "侧": "ce", "边": "bian", "底": "di", "顶": "ding",
    "端": "duan", "头": "tou", "尾": "wei", "始": "shi", "终": "zhong",
    "起": "qi", "止": "zhi", "源": "yuan", "汇": "hui", "流": "liu",
    "入": "ru", "出": "chu", "输": "shu", "入": "ru", "反": "fan",
    "馈": "kui", "闭": "bi", "环": "huan", "开": "kai", "放": "fang",
    "控": "kong", "制": "zhi", "调": "tiao", "节": "jie", "协": "xie",
    "同": "tong", "步": "bu", "异": "yi", "步": "bu", "同": "tong",
    "步": "bu", "串": "chuan", "行": "xing", "并": "bing", "行": "xing",
    "同": "tong", "步": "bu", "阻": "zu", "塞": "se", "非": "fei",
    "阻": "zu", "塞": "se", "异": "yi", "步": "bu", "多": "duo",
    "线": "xian", "程": "cheng", "单": "dan", "线": "xian", "程": "cheng",
    "协": "xie", "程": "cheng", "并": "bing", "发": "fa", "事": "shi",
    "件": "jian", "驱": "qu", "动": "dong", "消": "xiao", "息": "xi",
    "队": "dui", "列": "lie", "发": "fa", "布": "bu", "订": "ding",
    "阅": "yue", "观": "guan", "察": "cha", "者": "zhe", "模": "mo",
    "式": "shi", "策": "ce", "略": "lue", "工": "gong", "厂": "chang",
    "单": "dan", "例": "li", "原": "yuan", "型": "xing", "建": "jian",
    "造": "zao", "者": "zhe", "生": "sheng", "成": "cheng", "器": "qi",
    "迭": "die", "代": "dai", "器": "qi", "装": "zhuang", "饰": "shi",
    "器": "qi", "适": "shi", "配": "pei", "器": "qi", "桥": "qiao",
    "接": "jie", "器": "qi", "代": "dai", "理": "li", "器": "qi",
    "门": "men", "面": "mian", "组": "zu", "合": "he", "器": "qi",
    "解": "jie", "析": "xi", "器": "qi", "编": "bian", "码": "ma",
    "器": "qi", "序": "xu", "列": "lie", "化": "hua", "器": "qi",
    "缓": "huan", "冲": "chong", "池": "chi", "连": "lian", "接": "jie",
    "池": "chi", "线": "xian", "程": "cheng", "池": "chi", "资": "zi",
    "源": "yuan", "池": "chi", "对": "dui", "象": "xiang", "池": "chi",
    "内": "nei", "存": "cun", "池": "chi", "请": "qing", "求": "qiu",
    "池": "chi", "响": "xiang", "应": "ying", "池": "chi", "任": "ren",
    "务": "wu", "池": "chi", "工": "gong", "作": "zuo", "池": "chi",
    "进": "jin", "程": "cheng", "池": "chi", "服": "fu", "务": "wu",
    "池": "chi", "数": "shu", "据": "ju", "池": "chi", "缓": "huan",
    "存": "cun", "池": "chi", "存": "cun", "储": "chu", "池": "chi",
    "文": "wen", "件": "jian", "池": "chi", "图": "tu", "片": "pian",
    "池": "chi", "视": "shi", "频": "pin", "池": "chi", "音": "yin",
    "频": "pin", "池": "chi", "文": "wen", "档": "dang", "池": "chi",
    # ---- Common particles / prepositions / conjunctions ----
    "的": "de", "了": "le", "在": "zai", "是": "shi", "有": "you",
    "和": "he", "与": "yu", "及": "ji", "或": "huo", "但": "dan",
    "而": "er", "为": "wei", "以": "yi", "将": "jiang", "把": "ba",
    "被": "bei", "让": "rang", "给": "gei", "对": "dui", "向": "xiang",
    "于": "yu", "从": "cong", "到": "dao", "由": "you", "自": "zi",
    "至": "zhi", "据": "ju", "按": "an", "依": "yi", "照": "zhao",
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
    # ---- More common nouns / verbs ----
    "未": "wei", "已": "yi", "正": "zheng", "要": "yao", "需": "xu",
    "会": "hui", "能": "neng", "可": "ke", "应": "ying", "该": "gai",
    "得": "de", "地": "de", "着": "zhe", "过": "guo", "呢": "ne",
    "吧": "ba", "吗": "ma", "啊": "a", "哦": "o", "嗯": "en",
    "喂": "wei", "嗨": "hai", "嘿": "hei", "哈": "ha", "哟": "yo",
    "哇": "wa", "呀": "ya", "哪": "na", "啦": "la", "啰": "luo",
    "哩": "li", "喽": "lou", "嘞": "lei", "呗": "bei", "麽": "me",
    "某": "mou", "每": "mei", "各": "ge", "诸": "zhu", "凡": "fan",
    "凡": "fan", "皆": "jie", "悉": "xi", "全": "quan", "整": "zheng",
    "齐": "qi", "尽": "jin", "皆": "jie", "俱": "ju", "均": "jun",
    "统": "tong", "通": "tong", "普": "pu", "遍": "bian", "广": "guang",
    "泛": "fan", "宽": "kuan", "阔": "kuo", "博": "bo", "大": "da",
    "深": "shen", "厚": "hou", "重": "zhong", "浓": "nong", "密": "mi",
    "稀": "xi", "疏": "shu", "薄": "bo", "浅": "qian", "淡": "dan",
    "轻": "qing", "弱": "ruo", "强": "qiang", "猛": "meng", "烈": "lie",
    "剧": "ju", "激": "ji", "急": "ji", "紧": "jin", "迫": "po",
    "危": "wei", "险": "xian", "安": "an", "稳": "wen", "定": "ding",
    "静": "jing", "平": "ping", "稳": "wen", "顺": "shun", "畅": "chang",
    "通": "tong", "达": "da", "直": "zhi", "接": "jie", "快": "kuai",
    "慢": "man", "迟": "chi", "早": "zao", "速": "su", "迅": "xun",
    "捷": "jie", "敏": "min", "灵": "ling", "活": "huo", "巧": "qiao",
    "妙": "miao", "精": "jing", "准": "zhun", "确": "que", "正": "zheng",
    "真": "zhen", "假": "jia", "虚": "xu", "伪": "wei", "实": "shi",
    "诚": "cheng", "信": "xin", "忠": "zhong", "义": "yi", "仁": "ren",
    "爱": "ai", "善": "shan", "美": "mei", "好": "hao", "良": "liang",
    "优": "you", "秀": "xiu", "杰": "jie", "出": "chu", "卓": "zhuo",
    "越": "yue", "辉": "hui", "煌": "huang", "灿": "can", "烂": "lan",
    "耀": "yao", "眼": "yan", "夺": "duo", "目": "mu", "引": "yin",
    "吸": "xi", "诱": "you", "惑": "huo", "迷": "mi", "醉": "zui",
    "沉": "chen", "浸": "jin", "陷": "xian", "落": "luo", "坠": "zhui",
    "跌": "die", "倒": "dao", "摔": "shuai", "爬": "pa", "起": "qi",
    "站": "zhan", "立": "li", "坐": "zuo", "卧": "wo", "躺": "tang",
    "睡": "shui", "醒": "xing", "梦": "meng", "幻": "huan", "想": "xiang",
    "念": "nian", "思": "si", "考": "kao", "虑": "lv", "谋": "mou",
    "划": "hua", "策": "ce", "计": "ji", "议": "yi", "论": "lun",
    "谈": "tan", "说": "shuo", "讲": "jiang", "诉": "su", "告": "gao",
    "知": "zhi", "晓": "xiao", "懂": "dong", "明": "ming", "白": "bai",
    "清": "qing", "楚": "chu", "透": "tou", "彻": "che", "深": "shen",
    "奥": "ao", "玄": "xuan", "妙": "miao", "奇": "qi", "怪": "guai",
    "异": "yi", "特": "te", "殊": "shu", "稀": "xi", "罕": "han",
    "少": "shao", "多": "duo", "众": "zhong", "群": "qun", "集": "ji",
    "聚": "ju", "散": "san", "分": "fen", "离": "li", "合": "he",
    "并": "bing", "拆": "chai", "解": "jie", "组": "zu", "装": "zhuang",
    "配": "pei", "搭": "da", "调": "tiao", "协": "xie", "配": "pei",
    "适": "shi", "应": "ying", "合": "he", "符": "fu", "合": "he",
    "匹": "pi", "配": "pei", "对": "dui", "等": "deng", "同": "tong",
    "异": "yi", "差": "cha", "距": "ju", "别": "bie", "区": "qu",
    "分": "fen", "类": "lei", "型": "xing", "种": "zhong", "类": "lei",
    "品": "pin", "牌": "pai", "名": "ming", "号": "hao", "称": "cheng",
    "呼": "hu", "叫": "jiao", "喊": "han", "唤": "huan", "召": "zhao",
    "集": "ji", "招": "zhao", "聘": "pin", "请": "qing", "邀": "yao",
    "约": "yue", "订": "ding", "定": "ding", "约": "yue", "盟": "meng",
    "誓": "shi", "约": "yue", "契": "qi", "约": "yue", "合": "he",
    "同": "tong", "协": "xie", "议": "yi", "条": "tiao", "约": "yue",
    "章": "zhang", "程": "cheng", "规": "gui", "则": "ze", "法": "fa",
    "律": "lv", "令": "ling", "命": "ming", "令": "ling", "禁": "jin",
    "止": "zhi", "许": "xu", "可": "ke", "准": "zhun", "批": "pi",
    "核": "he", "查": "cha", "检": "jian", "验": "yan", "证": "zheng",
    "明": "ming", "示": "shi", "表": "biao", "露": "lu", "现": "xian",
    "显": "xian", "露": "lu", "出": "chu", "溢": "yi", "流": "liu",
    "淌": "tang", "滴": "di", "落": "luo", "溅": "jian", "喷": "pen",
    "射": "she", "发": "fa", "射": "she", "放": "fang", "释": "shi",
    "放": "fang", "排": "pai", "泄": "xie", "排": "pai", "出": "chu",
    "除": "chu", "去": "qu", "消": "xiao", "灭": "mie", "杀": "sha",
    "死": "si", "亡": "wang", "灭": "mie", "绝": "jue", "终": "zhong",
    "止": "zhi", "停": "ting", "休": "xiu", "息": "xi", "歇": "xie",
    "眠": "mian", "睡": "shui", "梦": "meng", "幻": "huan", "影": "ying",
    "像": "xiang", "形": "xing", "状": "zhuang", "态": "tai", "势": "shi",
    "姿": "zi", "势": "shi", "样": "yang", "子": "zi", "貌": "mao",
    "相": "xiang", "容": "rong", "貌": "mao", "面": "mian", "孔": "kong",
    "脸": "lian", "色": "se", "神": "shen", "情": "qing", "表": "biao",
    "情": "qing", "眼": "yan", "神": "shen", "目": "mu", "光": "guang",
    "视": "shi", "线": "xian", "注": "zhu", "视": "shi", "凝": "ning",
    "望": "wang", "眺": "tiao", "望": "wang", "仰": "yang", "望": "wang",
    "俯": "fu", "视": "shi", "瞰": "kan", "眺": "tiao", "瞩": "zhu",
    "目": "mu", "留": "liu", "意": "yi", "注": "zhu", "意": "yi",
    "专": "zhuan", "心": "xin", "致": "zhi", "志": "zhi", "聚": "ju",
    "精": "jing", "会": "hui", "神": "shen", "全": "quan", "神": "shen",
    "贯": "guan", "注": "zhu", "屏": "ping", "息": "xi", "凝": "ning",
    "神": "shen", "静": "jing", "气": "qi", "平": "ping", "心": "xin",
    "静": "jing", "气": "qi", "冷": "leng", "静": "jing", "镇": "zhen",
    "定": "ding", "沉": "chen", "着": "zhe", "稳": "wen", "重": "zhong",
    "从": "cong", "容": "rong", "淡": "dan", "定": "ding", "泰": "tai",
    "然": "ran", "自": "zi", "若": "ruo", "悠": "you", "然": "ran",
    "闲": "xian", "适": "shi", "舒": "shu", "适": "shi", "惬": "qie",
    "意": "yi", "痛": "tong", "快": "kuai", "爽": "shuang", "快": "kuai",
    "欢": "huan", "乐": "le", "喜": "xi", "悦": "yue", "愉": "yu",
    "快": "kuai", "高": "gao", "兴": "xing", "兴": "xing", "奋": "fen",
    "激": "ji", "动": "dong", "热": "re", "情": "qing", "激": "ji",
    "昂": "ang", "昂": "ang", "扬": "yang", "振": "zhen", "奋": "fen",
    "鼓": "gu", "舞": "wu", "激": "ji", "励": "li", "勉": "mian",
    "励": "li", "鞭": "bian", "策": "ce", "督": "du", "促": "cu",
    "催": "cui", "促": "cu", "逼": "bi", "迫": "po", "压": "ya",
    "榨": "zha", "挤": "ji", "压": "ya", "逼": "bi", "迫": "po",
    "强": "qiang", "迫": "po", "胁": "xie", "迫": "po", "恐": "kong",
    "吓": "xia", "威": "wei", "胁": "xie", "恐": "kong", "惧": "ju",
    "害": "hai", "怕": "pa", "畏": "wei", "惧": "ju", "胆": "dan",
    "怯": "qie", "懦": "nuo", "弱": "ruo", "退": "tui", "缩": "suo",
    "逃": "tao", "避": "bi", "躲": "duo", "藏": "cang", "隐": "yin",
    "瞒": "man", "掩": "yan", "饰": "shi", "遮": "zhe", "盖": "gai",
    "遮": "zhe", "掩": "yan", "伪": "wei", "装": "zhuang", "假": "jia",
    "扮": "ban", "模": "mo", "仿": "fang", "效": "xiao", "学": "xue",
    "习": "xi", "练": "lian", "习": "xi", "训": "xun", "练": "lian",
    "操": "cao", "练": "lian", "演": "yan", "习": "xi", "实": "shi",
    "战": "zhan", "演": "yan", "练": "lian", "操": "cao", "作": "zuo",
    "运": "yun", "行": "xing", "启": "qi", "动": "dong", "开": "kai",
    "始": "shi", "终": "zhong", "止": "zhi", "停": "ting", "关": "guan",
    "闭": "bi", "封": "feng", "锁": "suo", "禁": "jin", "锢": "gu",
    "囚": "qiu", "困": "kun", "绑": "bang", "缚": "fu", "捆": "kun",
    "绑": "bang", "系": "xi", "结": "jie", "扣": "kou", "解": "jie",
    "开": "kai", "松": "song", "绑": "bang", "释": "shi", "放": "fang",
    "解": "jie", "脱": "tuo", "摆": "bai", "脱": "tuo", "逃": "tao",
    "离": "li", "远": "yuan", "离": "li", "隔": "ge", "绝": "jue",
    "断": "duan", "绝": "jue", "割": "ge", "裂": "lie", "撕": "si",
    "裂": "lie", "破": "po", "碎": "sui", "损": "sun", "坏": "huai",
    "毁": "hui", "灭": "mie", "消": "xiao", "逝": "shi", "逝": "shi",
    "去": "qu", "世": "shi", "亡": "wang", "故": "gu", "逝": "shi",
    "殁": "mo", "薨": "hong", "崩": "beng", "驾": "jia", "崩": "beng",
    "薨": "hong", "逝": "shi", "卒": "zu", "殁": "mo", "夭": "yao",
    "折": "zhe", "殇": "shang", "殒": "yun", "命": "ming", "毙": "bi",
    "命": "ming", "横": "heng", "死": "si", "惨": "can", "死": "si",
    "罹": "li", "难": "nan", "遇": "yu", "害": "hai", "遭": "zao",
    "殃": "yang", "受": "shou", "害": "hai", "被": "bei", "害": "hai",
    "受": "shou", "伤": "shang", "损": "sun", "伤": "shang", "创": "chuang",
    "伤": "shang", "痕": "hen", "疤": "ba", "印": "yin", "记": "ji",
    "号": "hao", "标": "biao", "记": "ji", "符": "fu", "号": "hao",
    "记": "ji", "录": "lu", "载": "zai", "登": "deng", "记": "ji",
    "注": "zhu", "册": "ce", "备": "bei", "案": "an", "存": "cun",
    "档": "dang", "归": "gui", "档": "dang", "收": "shou", "藏": "cang",
    "保": "bao", "管": "guan", "维": "wei", "护": "hu", "养": "yang",
    "修": "xiu", "理": "li", "整": "zheng", "治": "zhi", "理": "li",
    "处": "chu", "置": "zhi", "安": "an", "排": "pai", "布": "bu",
    "置": "zhi", "配": "pei", "置": "zhi", "调": "tiao", "配": "pei",
    "分": "fen", "配": "pei", "发": "fa", "放": "fang", "派": "pai",
    "送": "song", "递": "di", "传": "chuan", "达": "da", "转": "zhuan",
    "达": "da", "表": "biao", "达": "da", "表": "biao", "现": "xian",
    "展": "zhan", "示": "shi", "显": "xian", "示": "shi", "呈": "cheng",
    "现": "xian", "涌": "yong", "现": "xian", "冒": "mao", "出": "chu",
    "露": "lu", "头": "tou", "角": "jiao", "崭": "zhan", "露": "lu",
    "头": "tou", "角": "jiao", "脱": "tuo", "颖": "ying", "而": "er",
    "出": "chu", "崭": "zhan", "新": "xin", "全": "quan", "新": "xin",
    "崭": "zhan", "新": "xin", "焕": "huan", "然": "ran", "一": "yi",
    "新": "xin", "面": "mian", "目": "mu", "一": "yi", "新": "xin",
    "改": "gai", "头": "tou", "换": "huan", "面": "mian", "脱": "tuo",
    "胎": "tai", "换": "huan", "骨": "gu", "重": "zhong", "生": "sheng",
    "涅": "nie", "槃": "pan", "重": "zhong", "生": "sheng", "复": "fu",
    "活": "huo", "苏": "su", "醒": "xing", "复": "fu", "苏": "su",
    "恢": "hui", "复": "fu", "康": "kang", "复": "fu", "痊": "quan",
    "愈": "yu", "治": "zhi", "愈": "yu", "医": "yi", "治": "zhi",
    "疗": "liao", "救": "jiu", "治": "zhi", "抢": "qiang", "救": "jiu",
    "挽": "wan", "救": "jiu", "补": "bu", "救": "jiu", "补": "bu",
    "充": "chong", "填": "tian", "补": "bu", "充": "chong", "增": "zeng",
    "加": "jia", "添": "tian", "加": "jia", "附": "fu", "加": "jia",
    "追": "zhui", "加": "jia", "累": "lei", "加": "jia", "叠": "die",
    "加": "jia", "倍": "bei", "增": "zeng", "翻": "fan", "倍": "bei",
    "成": "cheng", "倍": "bei", "数": "shu", "增": "zeng", "几": "ji",
    "何": "he", "级": "ji", "数": "shu", "指": "zhi", "数": "shu",
    "级": "ji", "爆": "bao", "炸": "zha", "式": "shi", "增": "zeng",
    "长": "zhang", "井": "jing", "喷": "pen", "式": "shi", "爆": "bao",
    "发": "fa", "喷": "pen", "涌": "yong", "涌": "yong", "现": "xian",
    "大": "da", "量": "liang", "批": "pi", "量": "liang", "大": "da",
    "规": "gui", "模": "mo", "大": "da", "范": "fan", "围": "wei",
    "广": "guang", "泛": "fan", "普": "pu", "遍": "bian", "全": "quan",
    "面": "mian", "整": "zheng", "体": "ti", "全": "quan", "局": "ju",
    "宏": "hong", "观": "guan", "微": "wei", "观": "guan", "局": "ju",
    "部": "bu", "整": "zheng", "体": "ti", "个": "ge", "体": "ti",
    "单": "dan", "个": "ge", "独": "du", "立": "li", "孤": "gu",
    "立": "li", "单": "dan", "独": "du", "孤": "gu", "身": "shen",
    "孤": "gu", "单": "dan", "寂": "ji", "寞": "mo", "孤": "gu",
    "独": "du", "无": "wu", "助": "zhu", "无": "wu", "依": "yi",
    "无": "wu", "靠": "kao", "无": "wu", "着": "zhe", "落": "luo",
    "无": "wu", "处": "chu", "可": "ke", "去": "qu", "无": "wu",
    "路": "lu", "可": "ke", "走": "zou", "无": "wu", "计": "ji",
    "可": "ke", "施": "shi", "无": "wu", "法": "fa", "可": "ke",
    "想": "xiang", "无": "wu", "药": "yao", "可": "ke", "救": "jiu",
    "无": "wu", "力": "li", "回": "hui", "天": "tian", "无": "wu",
    "能": "neng", "为": "wei", "力": "li", "束": "shu", "手": "shou",
    "无": "wu", "策": "ce", "一": "yi", "筹": "chou", "莫": "mo",
    "展": "zhan", "束": "shu", "手": "shou", "待": "dai", "毙": "bi",
    "坐": "zuo", "以": "yi", "待": "dai", "毙": "bi", "听": "ting",
    "天": "tian", "由": "you", "命": "ming", "任": "ren", "人": "ren",
    "宰": "zai", "割": "ge", "人": "ren", "为": "wei", "刀": "dao",
    "俎": "zu", "我": "wo", "为": "wei", "鱼": "yu", "肉": "rou",
    "案": "an", "板": "ban", "上": "shang", "鱼": "yu", "肉": "rou",
    "待": "dai", "宰": "zai", "羔": "gao", "羊": "yang", "任": "ren",
    "人": "ren", "摆": "bai", "布": "bu", "随": "sui", "人": "ren",
    "摆": "bai", "布": "bu", "听": "ting", "人": "ren", "摆": "bai",
    "布": "bu", "任": "ren", "人": "ren", "驱": "qu", "使": "shi",
    "任": "ren", "人": "ren", "驱": "qu", "策": "ce", "任": "ren",
    "人": "ren", "驱": "qu", "遣": "qian", "任": "ren", "人": "ren",
    "摆": "bai", "弄": "nong", "任": "ren", "人": "ren", "捉": "zhuo",
    "弄": "nong", "任": "ren", "人": "ren", "捉": "zhuo", "布": "bu",
    "任": "ren", "人": "ren", "捉": "zhuo", "布": "bu", "任": "ren",
    "人": "ren", "捉": "zhuo", "布": "bu", "任": "ren", "人": "ren",
    "捉": "zhuo", "布": "bu", "任": "ren", "人": "ren", "捉": "zhuo",
    "布": "bu", "任": "ren", "人": "ren", "捉": "zhuo", "布": "bu",
    "任": "ren", "人": "ren", "捉": "zhuo", "布": "bu", "任": "ren",
    "人": "ren", "捉": "zhuo", "布": "bu", "任": "ren", "人": "ren",
    "捉": "zhuo", "布": "bu", "任": "ren", "人": "ren", "捉": "zhuo",
    "布": "bu", "任": "ren", "人": "ren", "捉": "zhuo", "布": "bu",
    "任": "ren", "人": "ren", "捉": "zhuo", "布": "bu", "任": "ren",
    "人": "ren", "捉": "zhuo", "布": "bu", "任": "ren", "人": "ren",
    "捉": "zhuo", "布": "bu", "任": "ren", "人": "ren", "捉": "zhuo",
    "布": "bu", "任": "ren", "人": "ren", "捉": "zhuo", "布": "bu",
}


def _pinyin(text: str) -> str:
    """Convert Chinese text to pinyin-ish slug."""
    result = []
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            py = _PINYIN.get(ch)
            if py:
                result.append(py)
            else:
                # Fallback: use unicode codepoint hex
                result.append(f"u{ord(ch):04x}")
        else:
            result.append(ch)
    return "".join(result)


# ------------------------------------------------------------------
# Slugify
# ------------------------------------------------------------------
def slugify(text: str, max_len: int = 32) -> str:
    """Convert text to sec- compatible slug."""
    text = text.strip().lower()
    # Convert Chinese chars to pinyin
    text = _pinyin(text)
    # Remove remaining non-alphanumeric chars except spaces
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # Collapse spaces to dashes
    text = re.sub(r"\s+", "-", text)
    # Remove leading dashes and digits-after-dash issue
    text = text.strip("-")
    if not text:
        text = "section"
    return text[:max_len]


# ------------------------------------------------------------------
# Anchor injection
# ------------------------------------------------------------------
def inject_anchors(content: str) -> str:
    """Add {#sec-xxx} anchors to ## and ### headings that don't have one."""
    seen: set[str] = set()

    def repl(match: re.Match) -> str:
        prefix = match.group(1)
        title = match.group(2).strip()
        existing = match.group(3)
        if existing:
            return match.group(0)
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


# ------------------------------------------------------------------
# Meta extraction
# ------------------------------------------------------------------
def extract_meta(content: str, rel_path: Path) -> dict:
    """Heuristically extract metadata from legacy doc content."""
    meta: dict = {
        "title": "",
        "version": "1.0.0",
        "status": "DRAFT",
        "author": "agent-migration",
        "date": "2026-06-10",
    }

    # Title: first # line
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if m:
        meta["title"] = m.group(1).strip()

    # Version from > 版本：xxx
    m = re.search(r"[>\*]*\s*版本[：:]\s*([^\n\|]+)", content)
    if m:
        v = m.group(1).strip()
        v = re.sub(r"^(PRD-000|HLD-001|DR-001)\s*", "", v)
        v = v.replace("v", "").replace(" ", "")
        if re.match(r"^\d+\.\d+", v):
            meta["version"] = v
        else:
            meta["version"] = "1.0.0"

    # Status from > 状态：xxx
    m = re.search(r"[>\*]*\s*状态[：:]\s*\*?\*?([^\n\*]+)\*?\*?", content)
    if m:
        st = m.group(1).strip().lower()
        if "frozen" in st or "冻结" in st or "已通过" in st:
            meta["status"] = "FROZEN"
        elif "draft" in st or "草稿" in st:
            meta["status"] = "DRAFT"
        elif "review" in st or "评审" in st:
            meta["status"] = "REVIEW"
        else:
            meta["status"] = "DRAFT"

    # Author from > 作者：xxx
    m = re.search(r"[>\*]*\s*作者[：:]\s*([^\n]+)", content)
    if m:
        author = m.group(1).strip()
        if "AI" in author or "Agent" in author:
            meta["author"] = "agent-pm"
        elif "architect" in author.lower():
            meta["author"] = "agent-architect"
        elif "developer" in author.lower():
            meta["author"] = "agent-developer"
        else:
            meta["author"] = "agent-migration"

    # Date from > 日期：xxx or > 冻结时间：xxx
    m = re.search(r"[>\*]*\s*(?:日期|冻结时间|设计日期)[：:]\s*([^\n]+)", content)
    if m:
        meta["date"] = m.group(1).strip()

    return meta


# ------------------------------------------------------------------
# Strip legacy meta block & changelog
# ------------------------------------------------------------------
_META_KEYWORDS = [
    "版本", "状态", "作者", "日期", "评审人", "冻结时间", "变更", "设计日期",
    "模块编号", "模块名称", "关联需求", "关联用户故事", "上游基线", "下游基线",
]


def _is_meta_block(lines: list[str], start: int, end: int) -> bool:
    """Check if a block of > lines is a legacy meta block."""
    block_text = "\n".join(lines[start:end])
    return any(kw in block_text for kw in _META_KEYWORDS)


def strip_legacy_meta(content: str) -> str:
    """Remove old > meta blocks and inline changelog tables from doc."""
    lines = content.splitlines()
    result: list[str] = []
    changelog_stripped = False
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # Skip initial > block (meta info) at very top
        if not result and line.startswith(">"):
            i += 1
            continue

        # Skip blank lines at very top
        if not result and line.strip() == "":
            i += 1
            continue

        # Detect and strip inline changelog table (修改记录 / 版本历史)
        if not changelog_stripped and ("修改记录" in line or "版本历史" in line or ("版本" in line and "日期" in line and "修改人" in line)):
            j = i
            while j < n and (lines[j].strip() == "" or lines[j].startswith("|") or lines[j].startswith(">")):
                j += 1
            i = j
            changelog_stripped = True
            continue

        # Detect and strip > meta blocks anywhere in doc
        if line.startswith(">"):
            j = i
            while j < n and lines[j].startswith(">"):
                j += 1
            if _is_meta_block(lines, i, j):
                # Also consume trailing blank lines
                while j < n and lines[j].strip() == "":
                    j += 1
                i = j
                continue

        result.append(line)
        i += 1

    return "\n".join(result)


# ------------------------------------------------------------------
# Build YAML front matter
# ------------------------------------------------------------------
def build_front_matter(
    doc_type: str,
    fragment_id: str,
    title: str,
    version: str,
    status: str,
    author: str,
    iteration: str,
    tags: list[str],
) -> str:
    """Build standard YAML front matter block."""
    level = DOC_TYPE_LEVEL_MAP.get(doc_type, "")
    # Escape quotes in title
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


# ------------------------------------------------------------------
# Main migration logic
# ------------------------------------------------------------------
def migrate_file(src: Path, iteration: str) -> tuple[str, str] | None:
    """Migrate a single legacy doc. Returns (new_content, fragment_id) or None."""
    try:
        content = src.read_text(encoding="utf-8-sig")
    except Exception as exc:
        print(f"  SKIP (read error): {src} — {exc}")
        return None

    # Determine doc_type from path
    rel = src.relative_to(Path("openspec/changes") / iteration)
    parts = rel.parts
    doc_type = "CHANGELOG"
    for part in parts[:-1]:
        if part in DOC_TYPE_MAP:
            doc_type = DOC_TYPE_MAP[part]
            break

    # Special files override
    if src.name in SPECIAL_FILES:
        doc_type, _ = SPECIAL_FILES[src.name]

    # Extract meta
    meta = extract_meta(content, rel)

    # Generate fragment_id
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

    # Strip legacy meta
    body = strip_legacy_meta(content)

    # Inject anchors
    body = inject_anchors(body)

    # Build front matter
    tags = [iteration]
    if doc_type in ("PRD", "ARCH", "DETAIL_DESIGN", "API_DESIGN", "DB_DESIGN"):
        tags.append("architecture")

    front = build_front_matter(
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
    return new_content, fragment_id


def _derive_seq(src: Path) -> int:
    """Derive a sequence number from filename."""
    name = src.stem
    # Try to extract leading number
    m = re.match(r"^(\d+)[-_]", name)
    if m:
        return int(m.group(1))
    # Hash-based fallback
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    return (h % 900) + 1  # 1-900


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
def main() -> None:
    iteration = "sdlc-visualizer"
    src_root = Path("openspec/changes") / iteration
    dst_root = src_root / "baseline"

    if not src_root.exists():
        print(f"Source directory not found: {src_root}")
        return

    md_files = sorted(src_root.rglob("*.md"))
    migrated: list[tuple[Path, str]] = []
    skipped: list[Path] = []

    for src in md_files:
        # Skip already-migrated files in baseline/, delta/, compiled/
        if any(p in src.parts for p in ("baseline", "delta", "compiled", "_meta")):
            continue
        # Skip non-doc files (progress trackers, plans, etc.)
        if src.name in (
            "progress.md", "plan.md", "tasks.md", "human-decisions.md",
            "master-flow.md", "prd-000-toc.md", "release-notes.md",
        ):
            skipped.append(src)
            continue

        result = migrate_file(src, iteration)
        if result is None:
            skipped.append(src)
            continue

        new_content, fragment_id = result
        rel = src.relative_to(src_root)
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(new_content, encoding="utf-8")
        migrated.append((rel, fragment_id))

    # Write manifest
    manifest_lines = [
        f"# Migration manifest for {iteration}",
        "",
        f"Migrated: {len(migrated)} files",
        f"Skipped: {len(skipped)} files",
        "",
        "## Migrated files",
        "",
    ]
    for rel, fid in migrated:
        manifest_lines.append(f"- `{rel}` → `{fid}`")
    if skipped:
        manifest_lines.extend(["", "## Skipped files", ""])
        for s in skipped:
            manifest_lines.append(f"- `{s.relative_to(src_root)}`")

    manifest_path = dst_root / "_migration-manifest.md"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    print(f"Migrated {len(migrated)} files to {dst_root}")
    print(f"Skipped {len(skipped)} files")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
