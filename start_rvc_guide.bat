@echo off
chcp 65001 >nul
echo ========================================
echo RVC 快速启动指南
echo ========================================
echo.
echo 训练数据信息:
echo   - 位置: %CD%\so-vits-svc-4.1-Stable\dataset\44k\unicorn\
echo   - 文件数: 124 个 WAV
echo   - 总时长: 约 18.7 分钟
echo   - 采样率: 44.1kHz
echo.
echo ========================================
echo 下一步操作:
echo ========================================
echo.
echo 1. 下载 RVC 整合包
echo    访问: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/releases
echo    下载最新的 win32.7z 文件
echo.
echo 2. 解压到桌面或任意位置
echo.
echo 3. 运行 go-web.bat 启动 RVC
echo.
echo 4. 在浏览器中打开 http://localhost:7865
echo.
echo 5. 训练步骤:
echo    a) 实验名称: unicorn
echo    b) 数据路径: %CD%\so-vits-svc-4.1-Stable\dataset\44k\unicorn
echo    c) 目标采样率: 40k 或 48k
echo    d) 点击"处理数据"
echo    e) 点击"提取特征"
echo    f) 设置训练参数并开始训练
echo.
echo ========================================
echo 推荐训练参数:
echo ========================================
echo   - 训练轮数: 200-500 epoch
echo   - 批次大小: 8-12
echo   - 保存频率: 每 50 epoch
echo   - F0 提取: rmvpe 或 harvest
echo.
echo 按任意键打开 RVC 下载页面...
pause >nul
start https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/releases
