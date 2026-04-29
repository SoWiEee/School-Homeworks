#include "SSAO.h"
#include <glm/gtc/type_ptr.hpp>

SSAO::SSAO(int w, int h) : width(w), height(h) {
    // 1. 載入 Shaders
    ssaoShader = new Shader("assets/shaders/debug_quad.vert", "assets/shaders/ssao.frag");
    ssaoBlurShader = new Shader("assets/shaders/debug_quad.vert", "assets/shaders/ssao_blur.frag");

    // 2. 建立 SSAO Framebuffer
    glGenFramebuffers(1, &ssaoFBO);
    glBindFramebuffer(GL_FRAMEBUFFER, ssaoFBO);

    glGenTextures(1, &ssaoColorBuffer);
    glBindTexture(GL_TEXTURE_2D, ssaoColorBuffer);
    // SSAO 結果只需要一個紅色通道 (0.0~1.0)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, width, height, 0, GL_RED, GL_FLOAT, NULL);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, ssaoColorBuffer, 0);

    if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE)
        std::cout << "SSAO Framebuffer not complete!" << std::endl;

    // 3. 建立 Blur Framebuffer
    glGenFramebuffers(1, &ssaoBlurFBO);
    glBindFramebuffer(GL_FRAMEBUFFER, ssaoBlurFBO);

    glGenTextures(1, &ssaoColorBufferBlur);
    glBindTexture(GL_TEXTURE_2D, ssaoColorBufferBlur);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, width, height, 0, GL_RED, GL_FLOAT, NULL);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, ssaoColorBufferBlur, 0);

    glBindFramebuffer(GL_FRAMEBUFFER, 0);

    // 4. 生成核心與噪聲
    generateKernel();
    generateNoiseTexture();
}

SSAO::~SSAO() {
    delete ssaoShader;
    delete ssaoBlurShader;
    // 記得 delete buffers...
}

float SSAO::lerp(float a, float b, float f) {
    return a + f * (b - a);
}

void SSAO::generateKernel() {
    std::uniform_real_distribution<GLfloat> randomFloats(0.0, 1.0);
    std::default_random_engine generator;

    // 生成 64 個隨機採樣點 (半球體)
    for (unsigned int i = 0; i < 64; ++i) {
        glm::vec3 sample(
            randomFloats(generator) * 2.0 - 1.0,
            randomFloats(generator) * 2.0 - 1.0,
            randomFloats(generator) // Z 軸 0~1 (半球)
        );
        sample = glm::normalize(sample);
        sample *= randomFloats(generator);

        // 讓採樣點更靠近原點 (Scale distribution)
        float scale = float(i) / 64.0;
        scale = lerp(0.1f, 1.0f, scale * scale);
        sample *= scale;

        ssaoKernel.push_back(sample);
    }
}

void SSAO::generateNoiseTexture() {
    std::uniform_real_distribution<GLfloat> randomFloats(0.0, 1.0);
    std::default_random_engine generator;
    std::vector<glm::vec3> ssaoNoise;

    // 4x4 的噪聲圖，用來旋轉 Kernel
    for (unsigned int i = 0; i < 16; i++) {
        glm::vec3 noise(
            randomFloats(generator) * 2.0 - 1.0,
            randomFloats(generator) * 2.0 - 1.0,
            0.0f // 繞著 Z 軸旋轉
        );
        ssaoNoise.push_back(noise);
    }

    glGenTextures(1, &noiseTexture);
    glBindTexture(GL_TEXTURE_2D, noiseTexture);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, 4, 4, 0, GL_RGB, GL_FLOAT, &ssaoNoise[0]);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT); // 必須 Repeat
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
}

void SSAO::Compute(unsigned int gPosition, unsigned int gNormal, const glm::mat4& projection, const glm::mat4& view) {
    glBindFramebuffer(GL_FRAMEBUFFER, ssaoFBO);
    glClear(GL_COLOR_BUFFER_BIT);

    ssaoShader->use();

    // 傳入 G-Buffer
    glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, gPosition);
    glActiveTexture(GL_TEXTURE1); glBindTexture(GL_TEXTURE_2D, gNormal);
    glActiveTexture(GL_TEXTURE2); glBindTexture(GL_TEXTURE_2D, noiseTexture);

    ssaoShader->setInt("gPosition", 0);
    ssaoShader->setInt("gNormal", 1);
    ssaoShader->setInt("texNoise", 2);

    // 傳入矩陣與核心
    ssaoShader->setMat4("projection", glm::value_ptr(projection));
    ssaoShader->setMat4("view", glm::value_ptr(view));

    for (unsigned int i = 0; i < 64; ++i)
        ssaoShader->setVec3("samples[" + std::to_string(i) + "]", ssaoKernel[i]);

    // 畫 Quad 觸發計算
    Primitives::renderQuad();
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
}

void SSAO::Blur() {
    glBindFramebuffer(GL_FRAMEBUFFER, ssaoBlurFBO);
    glClear(GL_COLOR_BUFFER_BIT);

    ssaoBlurShader->use();
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, ssaoColorBuffer);
    ssaoBlurShader->setInt("ssaoInput", 0);

    Primitives::renderQuad();
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
}