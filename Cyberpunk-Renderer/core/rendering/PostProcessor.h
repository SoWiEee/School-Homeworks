#pragma once
#include <glad/glad.h>
#include <iostream>
#include "../Shader.h"
#include "Primitives.h"

class PostProcessor {
public:
    unsigned int hdrFBO;
    unsigned int colorBuffers[2]; // 0: Scene, 1: Brightness
    unsigned int rboDepth;

    unsigned int pingpongFBO[2];
    unsigned int pingpongColorbuffers[2];

    int width, height;
    Shader* blurShader;
    Shader* finalShader;

    PostProcessor(int w, int h);
    ~PostProcessor(); // 記得實作 cleanup

    void BeginRender(); // 綁定 HDR FBO
    void EndRender();   // 解綁
    void RenderBloom(); // 執行 Ping-Pong Blur
    void RenderFinal(float exposure); // 合成並輸出到螢幕
};