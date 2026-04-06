# app.py
import streamlit as st
import pdfplumber
from docx import Document
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL
import io

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="AI 简历评估助手",
    page_icon="📋",
    layout="wide"
)

# 初始化 AI 客户端
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ============================================================
# 样式美化
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #4A90D9;
        margin-bottom: 2rem;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .score-number {
        font-size: 4rem;
        font-weight: 800;
    }
    .metric-card {
        background: #F8FAFC;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #4A90D9;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 辅助函数
# ============================================================
def parse_pdf(file_bytes):
    """读取 PDF 文件内容"""
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except ImportError:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def parse_docx(file_bytes):
    """读取 Word 文件内容"""
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs]).strip()

def extract_text(uploaded_file):
    """根据文件类型提取文本"""
    suffix = uploaded_file.name.lower().split('.')[-1]
    file_bytes = uploaded_file.getvalue()
    
    if suffix == 'pdf':
        return parse_pdf(file_bytes)
    elif suffix in ('doc', 'docx'):
        return parse_docx(file_bytes)
    elif suffix == 'txt':
        return file_bytes.decode('utf-8', errors='ignore')
    else:
        st.error(f"暂不支持 {suffix} 格式，请上传 PDF、Word 或 TXT 文件")
        return None

def call_llm(prompt, system_prompt="你是一位专业的产品经理和简历评估专家。"):
    """调用 LLM"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 调用失败: {str(e)}\n\n请检查：1) API Key 是否正确 2) 网络连接 3) API 余额是否充足"

def analyze_resume(resume_text, jd_text):
def rewrite_resume(resume_text, jd_text):
    """根据JD优化简历"""

    system_prompt = """你是一位资深求职顾问，擅长优化简历。
你的任务是：
1. 保留真实经历
2. 提升表达质量
3. 强化与JD的匹配度
4. 使用更专业、有说服力的表达"""

    prompt = f"""
请根据目标岗位优化这份简历：

【原始简历】
{resume_text}

【目标岗位JD】
{jd_text}

请输出：
1. 优化后的简历（结构清晰、表达专业）
2. 标注你优化了哪些地方（简要说明）

要求：
- 不要编造经历
- 用更强的动词（如“负责”→“主导”）
- 强调与岗位相关的能力
"""

    return call_llm(prompt, system_prompt)
    """分析简历与 JD 的匹配度"""
    system_prompt = """你是一位资深 HR 和产品经理，擅长简历筛选和人才评估。
请从以下维度进行专业分析：
1. 整体匹配度评分（0-100分）
2. 关键词匹配率
3. 经验相关性评估
4. 技能差距分析
5. 改进建议（具体、可操作）
6. 给 HR 的一句话推荐语"""

    prompt = f"""
## 简历内容：
{resume_text}

## 目标岗位 JD：
{jd_text}

请按以下 JSON 格式输出（确保是合法的 JSON）：
{{
    "overall_score": 分数(0-100),
    "keyword_match_rate": "匹配率描述",
    "experience_analysis": "经验相关性分析",
    "skills_gap": ["差距1", "差距2"],
    "suggestions": ["建议1", "建议2", "建议3"],
    "hr_comment": "一句话推荐语"
}}
"""
    return call_llm(prompt, system_prompt)

def parse_analysis_result(result_text):
    """解析 LLM 返回的结果"""
    import json, re
    # 尝试提取 JSON
    json_match = re.search(r'\{[\s\S]*\}', result_text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return None

def display_score_gauge(score_str):
    """提取数字分数并显示"""
    import re
    match = re.search(r'\d+', str(score_str))
    if match:
        return int(match.group())
    return 0

# ============================================================
# 主界面
# ============================================================
st.markdown('<div class="main-header">📋 AI 简历评估助手</div>', unsafe_allow_html=True)

# 顶部说明
st.markdown("""
<div style="text-align:center; color: #666; margin-bottom: 2rem;">
上传简历 + 粘贴岗位 JD → AI 智能分析匹配度 + 给出改进建议
</div>
""", unsafe_allow_html=True)

# 输入区域 - 左右分栏
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📄 上传简历")
    st.caption("支持 PDF、Word(.docx)、TXT 格式")
    uploaded_file = st.file_uploader(
        "拖拽或点击上传简历",
        type=['pdf', 'docx', 'doc', 'txt'],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.success(f"✅ 已上传: {uploaded_file.name}")
        with st.spinner("正在解析简历..."):
            resume_text = extract_text(uploaded_file)
        if resume_text:
            with st.expander("📖 查看简历内容"):
                st.text_area("简历全文", resume_text, height=250, label_visibility="collapsed", disabled=True)

with col2:
    st.markdown("### 💼 粘贴岗位 JD")
    st.caption("复制粘贴目标岗位的完整描述")
    jd_text = st.text_area(
        "输入岗位描述",
        placeholder="粘贴岗位 JD...\n\n例如：\n- 岗位：产品经理\n- 要求：3年以上经验，熟悉数据分析工具\n- 加分项：有 AI 产品经验",
        height=257,
        label_visibility="collapsed"
    )

# 评估按钮
st.divider()
analyze_col1, analyze_col2, analyze_col3 = st.columns([1, 2, 1])
with analyze_col2:
    analyze_button = st.button("🚀 开始评估", type="primary", use_container_width=True)

# ============================================================
# 分析结果展示
st.divider()

if st.button("✨ 一键优化简历", use_container_width=True):
    with st.spinner("🤖 正在帮你优化简历..."):
        new_resume = rewrite_resume(resume_text, jd_text)
    
    st.success("✅ 优化完成！")
    
    st.markdown("### ✨ 优化后的简历")
    st.text_area("结果", new_resume, height=400)
# ============================================================
if analyze_button:
    if not uploaded_file:
        st.warning("⚠️ 请先上传简历文件")
    elif not jd_text.strip():
        st.warning("⚠️ 请粘贴岗位 JD 内容")
    elif not resume_text:
        st.error("❌ 简历解析失败，请尝试上传 TXT 格式的简历")
    else:
        with st.spinner("🤖 AI 正在分析中，请稍候..."):
            result = analyze_resume(resume_text, jd_text)
        
        st.success("✅ 分析完成！")
        parsed = parse_analysis_result(result)
        
        if parsed:
            # ---- 大分数展示 ----
            score = parsed.get("overall_score", display_score_gauge(result))
            
            # 根据分数选择颜色
            if score >= 80:
                score_color = "#22C55E"
                score_label = "🌟 高度匹配"
            elif score >= 60:
                score_color = "#F59E0B"
                score_label = "👍 较好匹配"
            else:
                score_color = "#EF4444"
                score_label = "⚠️ 匹配度待提升"
            
            st.markdown(f"""
            <div class="score-card">
                <div class="score-number" style="color: white;">{score}</div>
                <div style="font-size: 1.5rem; margin-top: 0.5rem;">分</div>
                <div style="margin-top: 1rem; font-size: 1.2rem;">{score_label}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # ---- 详细分析 Tab ----
            tab1, tab2, tab3 = st.tabs(["📊 匹配分析", "💡 改进建议", "📝 完整报告"])
            
            with tab1:
                col_km, col_ea = st.columns(2)
                with col_km:
                    st.markdown("#### 🔑 关键词匹配")
                    st.info(parsed.get("keyword_match_rate", "数据解析中..."))
                with col_ea:
                    st.markdown("#### 📈 经验相关性")
                    st.info(parsed.get("experience_analysis", "数据解析中..."))
                
                skills_gap = parsed.get("skills_gap", [])
                if skills_gap:
                    st.markdown("#### ⚡ 技能差距")
                    for skill in skills_gap:
                        st.markdown(f"- 🔸 {skill}")
            
            with tab2:
                st.markdown("#### 🎯 可操作的改进建议")
                suggestions = parsed.get("suggestions", [])
                if suggestions:
                    for i, s in enumerate(suggestions, 1):
                        st.markdown(f"""
                        <div class="metric-card">
                            <strong>建议 {i}:</strong> {s}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("暂无具体建议")
            
            with tab3:
                st.markdown("#### 📋 HR 推荐语")
                st.markdown(f"""
                > {parsed.get("hr_comment", "暂无推荐语")}
                """)
                
                st.markdown("#### 🔍 原始分析结果")
                st.text(result)
        else:
            # JSON 解析失败，直接展示原始文本
            st.markdown("#### 🔍 分析结果")
            st.markdown(result)

# ============================================================
# 底部信息
# ============================================================
st.divider()
st.markdown("""
<div style="text-align:center; color: #999; font-size: 0.85rem; margin-top: 2rem;">
Made with ❤️ by PM · Built with Streamlit + AI · 
<a href="https://github.com" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True)
