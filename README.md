# AI 简历评估助手

将简历与目标岗位逐条对照，指出缺少的依据，并给出修改建议。个人 AI 产品项目。

公开入口：https://jing845.github.io/-resume-analyzer/

在线工具：https://jf4mohp3dpaygr26enr5oj.streamlit.app/

## 使用

1. 粘贴简历，或上传文字型 PDF、DOCX、TXT。
2. 粘贴目标岗位要求。
3. 确认同意发送内容，点击“开始评估”。

默认直接显示输入表单。不了解如何填写时，可以点“填入示例”：填入一份虚构材料，再点“查看示例结果”查看明确标注的预置报告，不调用模型。修改材料后恢复真实评估流程。

报告包含简历原文依据、分析和修改建议。支持报告下载，以及真实评估后的经历改写建议。引用定位与新增数字等检查是辅助规则，仍须人工核对。未体现不等于没有能力，结果不预测录用概率。

## 部署

Streamlit 使用根目录的 app.py、core.py、config.py、samples.json 和 requirements.txt。API_KEY 仅保存在 Streamlit Settings → Secrets 中，不要提交到 GitHub。BASE_URL 和 MODEL 为可选覆盖配置。

默认服务地址为硅基流动兼容接口，默认模型为 Qwen/Qwen2.5-7B-Instruct，实际价格和可用性以服务商为准。最近一次真实调用仍遇到 402 额度错误，界面更新不表示模型账户问题已恢复。

GitHub Pages 从 main 分支的 /docs 发布。docs/index.html 为不依赖外部资源的极简入口，不接收简历、不调用模型。点击主按钮进入 Streamlit；首次打开可能需要等待，免费服务及网络均有可用性限制。

## 本地运行

安装 requirements.txt，配置 API_KEY 后运行 streamlit run app.py。不配置密钥也可使用可选预置示例。

## 验证

核心处理逻辑此前通过 13 项检查。本次简化界面后通过 5 项流程检查，覆盖空白默认页面、可选示例、提交同意、输入变化清理、错误处理与结果保留，真实模型响应使用模拟数据。未据此宣称模型效果或求职效果提升。
