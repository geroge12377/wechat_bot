# SoVITS 502/500 错误解决方案

## 问题诊断

当前状态：
- ✅ SoVITS 服务运行正常 (localhost:9872)
- ✅ API 端点可访问
- ✅ 模型切换 API 返回 200
- ❌ TTS 推理返回 500/502 错误

## 根本原因

**SoVITS 模型未通过 WebUI 加载！**

虽然 API 可以访问，但实际的 GPT 和 SoVITS 模型需要通过 WebUI 界面手动选择并加载后才能使用。

## 解决步骤

### 1. 打开 SoVITS WebUI

在浏览器中访问：
```
http://localhost:9872
```

### 2. 加载 GPT 模型

在 WebUI 界面中：
1. 找到 "GPT模型选择" 下拉菜单
2. 选择：`GPT_weights_v2Pro/xxx-e50.ckpt`
3. 点击"加载模型"或等待自动加载

### 3. 加载 SoVITS 模型

在 WebUI 界面中：
1. 找到 "SoVITS模型选择" 下拉菜单
2. 选择一个 SoVITS 模型（例如：`SoVITS_weights_v2Pro/unicorn_e8_s352.pth`）
3. 点击"加载模型"或等待自动加载

### 4. 验证模型加载

在 WebUI 中：
1. 上传一个参考音频（例如：`D:\GPT_SoVITS\raw\unicorn\unicorn_anniversary_01.wav`）
2. 输入测试文本："你好呀"
3. 点击"生成"按钮
4. 如果能生成音频，说明模型加载成功

### 5. 重新测试 API

模型加载成功后，运行：
```bash
python test_real_audio.py
```

应该返回 200 状态码。

## 替代方案：使用简化版本

如果 SoVITS 配置复杂，可以先使用不含 TTS 的简化版本：

```bash
python test_simple_bot.py
```

这个版本只使用 RAG + LLM，不调用 SoVITS，可以验证其他功能是否正常。

## 常见问题

### Q: 为什么 API 返回 200 但推理失败？

A: `/api/change_choices` 只是切换模型选择，但不会实际加载模型。模型需要通过 WebUI 加载到内存中。

### Q: 如何确认模型已加载？

A: 在 WebUI 中成功生成一次音频后，模型就已经加载到内存中了。

### Q: 可以通过 API 加载模型吗？

A: 理论上可以，但 GPT-SoVITS 的 API 设计需要先通过 WebUI 初始化模型。

## 自动化脚本（高级）

如果需要自动化，可以考虑：

1. 使用 Selenium 自动化 WebUI 操作
2. 直接调用 GPT-SoVITS 的内部 Python API
3. 修改 GPT-SoVITS 源码添加模型自动加载

## 下一步

1. ⏳ 打开 WebUI (http://localhost:9872)
2. ⏳ 手动加载 GPT 和 SoVITS 模型
3. ⏳ 在 WebUI 中测试生成音频
4. ⏳ 重新运行 `python wechat_bot_integrated.py`

## 参考

- GPT-SoVITS 文档: https://github.com/RVC-Boss/GPT-SoVITS
- WebUI 端口: http://localhost:9872
- 模型路径: `GPT_weights_v2Pro/xxx-e50.ckpt`
- 音频路径: `D:\GPT_SoVITS\raw\unicorn\`
