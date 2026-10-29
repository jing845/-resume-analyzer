"""AI resume evidence assistant — example first, live analysis on demand."""
import hashlib
import html
import json
from pathlib import Path

import streamlit as st

from config import get_settings
from core import STATUS_LABELS, UserError, analyze, extract_text, report_markdown, rewrite

st.set_page_config(page_title="简历诊断助手", page_icon="📄", layout="wide")
SAMPLES = json.loads(Path(__file__).with_name("samples.json").read_text(encoding="utf-8"))

st.markdown("""<style>
.stApp{background:#f7f7f2;color:#202b34} .block-container{max-width:1120px;padding-top:2.4rem}
h1,h2,h3{letter-spacing:-.035em} .eyebrow{color:#3157d7;font-size:.82rem;letter-spacing:.12em;margin-bottom:.7rem}
.intro{max-width:680px;color:#58646b;line-height:1.8;margin-bottom:1.4rem}
.evidence{padding:14px 18px;background:#edf0f6;border-left:3px solid #3157d7;border-radius:4px;line-height:1.8}
.stButton>button[kind=primary]{background:#3157d7;border-color:#3157d7;border-radius:8px}
[data-testid=stMetric]{background:#fff;padding:16px;border:1px solid #e1e4e6;border-radius:10px}
@media(max-width:600px){.block-container{padding:1.2rem}h1{font-size:2rem!important}}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="eyebrow">AI 简历诊断 · 个人产品项目</div>', unsafe_allow_html=True)
st.title("看清岗位要求，写好真实经历。")
st.markdown('<div class="intro">把简历与目标岗位放在一起，逐条查看对应证据、待补信息与改写建议。先查看示例，也可以直接粘贴自己的简历开始评估。</div>', unsafe_allow_html=True)


def render_report(report, prefix):
    st.markdown(report["summary"])
    rows = report["requirements"]
    cols = st.columns(3)
    for col, status in zip(cols, ("matched", "partial", "not_shown")):
        col.metric(STATUS_LABELS[status], sum(row["status"] == status for row in rows))
    st.caption("以上为岗位要求条数，不是录用概率。未体现不等于不具备；有引用也需结合上下文人工核对。")
    if any(row["status"] == "verify" for row in rows):
        st.warning("部分引用未在原文定位，已标记待核对，未计入已体现数量。")
    for index, row in enumerate(rows):
        label = "加分项" if row["kind"] == "preferred" else "岗位要求"
        with st.expander(f'{STATUS_LABELS[row["status"]]} · {row["requirement"]}', expanded=index == 0):
            st.caption(label + " · " + row["priority"])
            st.markdown("**简历依据**")
            if row["evidence"]:
                st.markdown('<div class="evidence">' + html.escape(row["evidence"]) + '</div>', unsafe_allow_html=True)
            else:
                st.caption("没有定位到对应原文。")
            st.markdown("**判断**　" + row["reason"])
            st.markdown("**下一步**　" + row["action"])
    if report.get("questions"):
        st.markdown("#### 你可以补充的信息")
        for question in report["questions"]:
            st.markdown("- " + question)
    st.download_button("下载核对报告", report_markdown(report), file_name="简历岗位核对报告.md", mime="text/markdown", key=prefix + "_download")


example_tab, live_tab, about_tab = st.tabs(["先看示例", "评估我的简历", "项目说明"])
with example_tab:
    st.caption(SAMPLES["notice"] + "。此处不调用模型，方便直接查看产品流程。")
    title = st.radio("选择目标岗位", [job["title"] for job in SAMPLES["jobs"]], horizontal=True, key="sample_job")
    job = next(item for item in SAMPLES["jobs"] if item["title"] == title)
    with st.expander("查看虚构简历与岗位要求"):
        st.text(SAMPLES["resume"])
        st.markdown("**目标岗位**")
        st.write(job["jd"])
    render_report(job["report"], "sample_" + job["id"])
    st.markdown("#### 一段真实边界内的表达优化")
    left, right = st.columns(2)
    left.markdown("**原表达**")
    left.write(SAMPLES["rewrite"]["original"])
    right.markdown("**改写示例**")
    right.write(SAMPLES["rewrite"]["revised"])
    st.caption(SAMPLES["rewrite"]["reason"])

with live_tab:
    st.info("实时分析会将你提交的简历文本和 JD 发送给硅基流动模型服务。建议先去掉电话、邮箱及其他不相关个人信息。本应用不主动写入简历数据库。")
    mode = st.radio("简历输入方式", ["粘贴文本", "上传文件"], horizontal=True)
    resume = ""
    if mode == "粘贴文本":
        resume = st.text_area("简历内容", height=240, max_chars=18000, placeholder="粘贴教育、经历与技能等内容……", key="resume_input")
    else:
        upload = st.file_uploader("上传简历（不超过 5 MB）", type=["pdf", "docx", "txt", "doc"], help="支持文字型 PDF、DOCX 和 TXT。旧版 DOC 会提示转换，不会进入分析。")
        st.caption("支持文字型 PDF、DOCX、TXT。旧版 DOC 需另存；扫描件暂不支持。")
        if upload:
            try:
                resume = extract_text(upload.name, upload.getvalue())
                with st.expander("检查提取的文字", expanded=True):
                    st.text_area("解析结果（请检查是否缺字或顺序异常）", resume, height=180, disabled=True, key="parsed_preview")
            except UserError as error:
                st.warning(str(error))
    jd = st.text_area("目标岗位 JD", height=180, max_chars=10000, placeholder="粘贴岗位职责、任职要求及加分项……", key="jd_input")
    consent = st.checkbox("我同意将上述文本发送至硅基流动以生成分析。", key="model_consent")
    fingerprint = hashlib.sha256((resume + "\x00" + jd).encode()).hexdigest()
    if st.session_state.get("live_fingerprint") != fingerprint:
        st.session_state["live_fingerprint"] = fingerprint
        st.session_state.pop("live_report", None)
        st.session_state.pop("live_rewrites", None)
    if st.button("开始核对岗位证据", type="primary", use_container_width=True):
        if not consent:
            st.warning("请先确认是否同意发送上述文本。也可直接查看示例，无需提交材料。")
        else:
            try:
                with st.spinner("正在拆解岗位要求并核对简历证据，请稍候……"):
                    report = analyze(get_settings(), resume, jd)
                st.session_state["live_report"] = report
                st.session_state.pop("live_rewrites", None)
                st.success("核对完成，请逐条检查依据。")
            except UserError as error:
                st.error(str(error))
    if st.session_state.get("live_report"):
        render_report(st.session_state["live_report"], "live")
        st.divider()
        st.markdown("#### 核对事实后，再改善表达")
        st.caption("先补全真实信息。下面只调整已有表达；数字和职责检查是辅助规则，结果仍需你确认。")
        if st.button("生成逐段改写建议", use_container_width=True):
            if not consent:
                st.warning("请先确认是否同意将文本发送给模型服务。")
            else:
                try:
                    with st.spinner("正在对照原文生成保守改写……"):
                        st.session_state["live_rewrites"] = rewrite(get_settings(), resume, jd)
                except UserError as error:
                    st.error(str(error))
        for index, change in enumerate(st.session_state.get("live_rewrites", []), 1):
            st.markdown(f"**建议 {index}**")
            before, after = st.columns(2)
            before.markdown("原文")
            before.write(change["original"])
            after.markdown("建议表达")
            after.write(change["revised"])
            st.caption(change["reason"])
            for note in change["checks"]:
                st.warning(note)
            st.checkbox("我已核对这一段的角色、数字和事实。", key=f"confirm_{fingerprint}_{index}")

with about_tab:
    st.markdown("### 从一个分数，走向可检查的依据")
    st.write("求职者需要知道哪里有证据、哪里需要补充，以及下一步能怎么改。这个版本将 JD 拆成要求，对照简历原文，再给出行动建议；不预测录用概率。")
    st.markdown("**已实现**：虚构样例体验、文本／文件输入、逐条证据核对、引用定位检查、逐段表达建议、结果下载和失败提示。")
    st.markdown("**边界**：模型可能漏判或误判；引用定位仅检查原文是否存在，不能证明解释正确。扫描件暂不支持。示例是预置内容，实时评估在明确提交后调用服务。")
    st.markdown("**后续验证**：用不同岗位和简历测试证据引用、缺失信息识别及改写事实保持情况，保留真实案例后再报告效果。")

st.divider()
st.caption("个人产品项目 · 本工具用于求职材料梳理，不代替招聘决定。")
st.markdown("[查看项目源码](https://github.com/jing845/-resume-analyzer)")
