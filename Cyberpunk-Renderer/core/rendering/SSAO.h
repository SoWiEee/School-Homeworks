#pragma once
#include <glad/glad.h>
#include <glm/glm.hpp>
#include <vector>
#include <random>
#include "../Shader.h"
#include "../GBuffer.h"
#include "../Camera.h"
#include "Primitives.h"

class SSAO {
public:
    unsigned int ssaoFBO, ssaoBlurFBO;
    unsigned int ssaoColorBuffer, ssaoColorBufferBlur;
    unsigned int noiseTexture;

    std::vector<glm::vec3> ssaoKernel;
    Shader* ssaoShader;
    Shader* ssaoBlurShader;

    int width, height;

    SSAO(int w, int h);
    ~SSAO();

    // 計算 SSAO (讀取 G-Buffer，輸出到 ssaoColorBuffer)
    void Compute(unsigned int gPosition, unsigned int gNormal, const glm::mat4& projection, const glm::mat4& view);

    // 模糊 SSAO (去除噪點)
    void Blur();

    // 取得最終結果貼圖 ID
    unsigned int GetSSAOTexture() { return ssaoColorBufferBlur; }

private:
    void generateKernel();
    void generateNoiseTexture();
    float lerp(float a, float b, float f);
};