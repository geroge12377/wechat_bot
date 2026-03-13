# SoVITS 参考音频问题诊断结果

## 测试结果

✅ **不使用参考音频**: TTS 推理成功（200）
❌ **使用参考音频**: TTS 推理失败（500）

## 根本原因

SoVITS 模型未完全初始化。虽然 API 可以访问，但使用参考音频的功能需要通过 WebUI 完全加载模型后才能使用。

## 解决方案

### 必须执行的步骤：

1. **打开 WebUI**
   ```
   浏览器访问: http://localhost:9872
   ```

2. **加载 GPT 模型**
   - 在 WebUI 中找到 "GPT模型选择" 下拉菜单
   - 选择: `GPT_weights_v2Pro/xxx-e50.ckpt`
   - 等待模型加载完成

3. **加载 SoVITS 模型**
   - 在 WebUI 中找到 "SoVITS模型选择" 下拉菜单
   - 选择一个模型（例如: `SoVITS_weights_v2Pro/unicorn_e8_s352.pth`）
   - 等待模型加载完成

4. **测试参考音频**
   - 在 WebUI 中上传参考音频: `D:\GPT_SoVITS\raw\unicorn\unicorn_battle_25.wav`
   - 输入测试文本: "你好呀"
   - 点击"生成"按钮
   - 如果能成功生成音频，说明模型已完全初始化

5. **重新测试 API**
   ```bash
   python test_with_ref_final.py
   ```
   应该返回 200 状态码。

## 临时解决方案

如果暂时无法通过 WebUI 初始化，可以使用不带参考音频的版本：

```python
# 在 unicorn_scheduler.py 中修改
async def _call_sovits_tts(self, text: str, ref_audio_path: str, temperature: float, top_p: float) -> bytes:
    # 暂时不使用参考音频
    payload = {
        "data": [
            text,
            "中文",
            None,  # 不使用参考音频
            [],
            "",
            "中文",
            5,
            top_p,
            temperature,
            "凑四句一切",
            1,
            1.0,
            False,
            True,
            0.3,
            -1,
            True,
            True,
            1.35,
            "128",
            False
        ]
    }
    # ... 其余代码不变
```

## 技术细节

- 测试了多种路径格式（绝对路径、相对路径、Unix风格、Windows风格）均失败
- 测试了 multipart/form-data 文件上传方式也失败
- 所有使用参考音频的请求都返回 `{"error":null}` 和 500 状态码
- 这表明是 SoVITS 内部处理参考音频时出错，而不是路径或格式问题

## 下一步

1. ⏳ 打开 WebUI (http://localhost:9872)
2. ⏳ 手动加载 GPT 和 SoVITS 模型
3. ⏳ 在 WebUI 中测试生成音频
4. ⏳ 重新运行 `python test_with_ref_final.py` 验证
5. ⏳ 如果成功，运行 `python wechat_bot_integrated.py` 测试完整流程
