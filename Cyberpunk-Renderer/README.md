# Cyberpunk-Renderer

一個以 **C++ / OpenGL 4.5** 實作的即時城市場景渲染專案，核心採用 **Deferred Shading**，並加入 **SSAO、Bloom、Skybox、Instancing** 等效果，呈現霓虹風格（Cyberpunk）夜景。

## 專案特色

- **Deferred Rendering Pipeline**
  - Geometry Pass：輸出 G-Buffer（位置、法線、材質資訊）
  - Lighting Pass：集中計算大量動態光源
  - Forward Pass：繪製光源幾何與天空盒
  - Post Process：Bloom / Blur / Final compositing
- **大量動態光源**：程式中建立約 200 個彩色點光源並做動畫。
- **Instanced Mesh**：批次繪製建築群，降低 draw call 開銷。
- **可自由移動相機**：滑鼠視角 + WASD 移動。

## 技術堆疊

- C++
- OpenGL 4.5 + GLAD
- GLFW
- GLM
- ImGui（vendor 內含）

## 專案結構

```text
Cyberpunk-Renderer/
├── main.cpp                        # 主程式：場景建立、render loop
├── core/
│   ├── Camera.*                    # 相機控制
│   ├── Shader.*                    # Shader 載入與 uniform 包裝
│   ├── GBuffer.h                   # G-buffer 定義
│   └── rendering/
│       ├── DeferredRenderer.*      # 多階段渲染流程
│       ├── SSAO.*                  # 環境光遮蔽
│       ├── PostProcessor.*         # 後處理（Bloom/Blur）
│       ├── SkyboxRenderer.*        # 天空盒
│       └── InstancedMesh.*         # Instancing 幾何
├── assets/shaders/                 # GLSL shader
└── assets/textures/                # 紋理資源
```

## 操作方式

- `W / A / S / D`：移動
- 滑鼠：視角旋轉
- 滾輪：視角縮放
- `ESC`：離開

## 建置（Windows / Visual Studio）

本資料夾已提供 `.sln` 與 `.vcxproj`，可直接開啟 `Cyberpunk-Renderer.sln` 建置。

若要手動建置，請先確認以下依賴可用：

- OpenGL runtime
- GLFW
- GLAD
- GLM

> 備註：本專案包含 `vendor/`（如 imgui、stb），其餘第三方路徑請依你的本機環境設定 include/lib。
