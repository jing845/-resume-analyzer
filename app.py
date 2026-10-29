"""A compact resume-to-job evaluation flow."""
import hashlib
import html
import json
from pathlib import Path

import streamlit as st

from config import get_settings
from core import STATUS_LABELS, UserError, analyze, extract_text, report_markdown, rewrite

st.set_page_config(page_title="AI 简历评估助手", page_icon="📄", layout="centered")
SAMPLES = json.loads(Path(__file__).with_name("samples.json").read_text(encoding="utf-8"))
SAMPLE_JOB = SAMPLES["jobs"][0]

st.markdown("""<style>
.block-container{max-width:860px;padding-top:2.5rem}
.evidence{padding:12px 15px;background:#f5f6f8;border-left:3px solid #5574b8;line-height:1.75}
@media(max-width:600px){.block-container{padding:1.3rem}h1{font-size:1.9rem!important}}
</style>""", unsafe_allow_html=True)
st.title("AI 简历评估助手")
st.write("对照目标岗位，找出简历的不足，并给出具体修改建议。")


def fill_example():
    st.session_state["resume_input"] = SAMPLES["resume"]
    st.session_state["jd_input"] = SAMPLE_JOB["jd"]
    st.session_state["model_consent"] = False
    st.session_state.pop("input_error", None)


def read_upload():
    upload = st.session_state.get("resume_upload")
    if upload:
        try:
            st.session_state["resume_input"] = extract_text(upload.name, upload.getvalue())
            st.session_state.pop("input_error", None)
        except UserError as error:
            st.session_state["input_error"] = str(error)


def render_report(report):
    st.subheader("评估结果")
    st.write(report["summary"])
    st.caption("未体现表示简历中缺少依据，不代表你没有这项能力。")
    for index, row in enumerate(report["requirements"]):
        with st.expander(f'{STATUS_LABELS[row["status"]]} · {row["requirement"]}', expanded=index == 0):
            if row["evidence"]:
                st.markdown("**简历原文**")
                st.markdown('<div class="evidence">' + html.escape(row["evidence"]) + '</div>', unsafe_allow_html=True)
            elif row["status"] == "verify":
                st.warning("模型引用未在简历原文定位，请人工核对。")
            else:
                st.caption("简历中没有找到对应依据。")
            st.markdown("**分析**　" + row["reason"])
            st.markdown("**修改建议**　" + row["action"])
    if report.get("questions"):
        st.markdown("**建议补充的信息**")
        for question in report["questions"]:
            st.write("• " + question)
    st.download_button("下载评估报告", report_markdown(report), file_name="简历评估报告.md", mime="text/markdown", key="live_download")


st.button("填入示例", on_click=fill_example, help="不知道怎么填写时，可用一份虚构材料查看预置结果。")
with st.expander("上传简历文件（也可以直接粘贴）"):
    st.file_uploader("支持 PDF、DOCX、TXT，最大 5 MB", type=["pdf", "docx", "txt", "doc"], key="resume_upload", on_change=read_upload)
    st.caption("仅支持可提取文字的文件；旧版 DOC 请另存为 DOCX，扫描件暂不支持。")
if st.session_state.get("input_error"):
    st.warning(st.session_state["input_error"])
resume = st.text_area("1. 简历内容", height=230, max_chars=18000, placeholder="粘贴你的教育背景、实习或项目经历、技能等内容。", key="resume_input")
jd = st.text_area("2. 目标岗位要求", height=160, max_chars=10000, placeholder="粘贴招聘信息中的岗位职责、任职要求。", key="jd_input")
is_example = resume == SAMPLES["resume"] and jd == SAMPLE_JOB["jd"]
if is_example:
    st.caption("当前是虚构示例。点击下方按钮查看预置结果，不调用 AI；修改内容后可进行真实评估。")
else:
    st.caption("请先删除电话、邮箱等无关个人信息。分析内容将发送至硅基流动模型服务，本应用不主动存入简历数据库。")
consent = st.checkbox("我同意将填写的内容发送给 AI 进行分析。", key="model_consent", disabled=is_example)
fingerprint = hashlib.sha256((resume + "\x00" + jd).encode()).hexdigest()
if st.session_state.get("live_fingerprint") != fingerprint:
    st.session_state["live_fingerprint"] = fingerprint
    st.session_state.pop("live_report", None)
    st.session_state.pop("live_rewrites", None)
if st.button("查看示例结果" if is_example else "开始评估", type="primary", use_container_width=True):
    if is_example:
        st.session_state["live_report"] = SAMPLE_JOB["report"]
    elif not resume.strip() or not jd.strip():
        st.warning("请先填写简历内容和目标岗位要求。")
    elif not consent:
        st.warning("请先勾选同意发送内容，再开始评估。")
    else:
        try:
            with st.spinner("正在对照岗位分析简历，请稍候……"):
                st.session_state["live_report"] = analyze(get_settings(), resume, jd)
            st.session_state.pop("live_rewrites", None)
        except UserError as error:
            st.error(str(error))
if st.session_state.get("live_report"):
    st.divider()
    if is_example:
        st.caption("示例结果 · 预置内容，非实时 AI 分析")
    render_report(st.session_state["live_report"])
    if not is_example:
        if st.button("生成经历改写建议"):
            if not consent:
                st.warning("请先勾选同意发送内容。")
            else:
                try:
                    with st.spinner("正在生成改写建议……"):
                        st.session_state["live_rewrites"] = rewrite(get_settings(), resume, jd)
                except UserError as error:
                    st.error(str(error))
        for index, change in enumerate(st.session_state.get("live_rewrites", []), 1):
            st.markdown(f"**改写建议 {index}**")
            st.markdown("**原文**")
            st.write(change["original"])
            st.markdown("**建议表达**")
            st.write(change["revised"])
            st.caption(change["reason"])
            for note in change["checks"]:
                st.warning(note)
            st.checkbox("我已核对角色、数字和事实。", key=f"confirm_{fingerprint}_{index}")

st.caption("AI 结果仅供参考，请核对事实。")
with st.expander("关于项目"):
    st.write("个人 AI 产品项目：将岗位要求与简历原文逐条对照，指出缺少的依据，并给出修改建议。引用定位与改写检查为辅助规则，不能替代人工判断。")
    st.markdown("[查看项目源码](https://github.com/jing845/-resume-analyzer)")
