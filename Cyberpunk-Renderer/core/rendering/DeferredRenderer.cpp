#include "DeferredRenderer.h"
#include <glm/gtc/type_ptr.hpp>
#include "stb_image.h"

DeferredRenderer::DeferredRenderer(int w, int h) : width(w), height(h) {
    gBuffer = new GBuffer(w, h);
    postProcessor = new PostProcessor(w, h);
    ssao = new SSAO(w, h);

    gBufferShader = new Shader("assets/shaders/gbuffer.vert", "assets/shaders/gbuffer.frag");
    lightingShader = new Shader("assets/shaders/deferred_shading.vert", "assets/shaders/deferred_shading.frag");
    lightBoxShader = new Shader("assets/shaders/light_box.vert", "assets/shaders/light_box.frag");

    lightingShader->use();
    lightingShader->setInt("gPosition", 0);
    lightingShader->setInt("gNormal", 1);
    lightingShader->setInt("gAlbedoSpec", 2);
    lightingShader->setInt("ssao", 3);
    lightingShader->setInt("gEmission", 4);

    buildingNormalMap = loadTexture("assets/textures/building_normal.jpg");
    gBufferShader->use();
    gBufferShader->setInt("normalMap", 1);
}

DeferredRenderer::~DeferredRenderer() {
    delete gBuffer;
    delete postProcessor;
    delete gBufferShader;
    delete lightingShader;
    delete lightBoxShader;
    delete ssao;
}

void DeferredRenderer::BeginGeometryPass(Camera& camera) {
    glBindFramebuffer(GL_FRAMEBUFFER, gBuffer->gBuffer);
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    gBufferShader->use();
    glm::mat4 projection = glm::perspective(glm::radians(camera.Zoom), (float)width / (float)height, 0.1f, 100.0f);
    glm::mat4 view = camera.GetViewMatrix();
    gBufferShader->setMat4("projection", glm::value_ptr(projection));
    gBufferShader->setMat4("view", glm::value_ptr(view));

    glActiveTexture(GL_TEXTURE1);
    glBindTexture(GL_TEXTURE_2D, buildingNormalMap);
}

void DeferredRenderer::EndGeometryPass() {
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
}

void DeferredRenderer::BeginLightingPass(Camera& camera) {
    // 1. SSAO
    glm::mat4 projection = glm::perspective(glm::radians(camera.Zoom), (float)width / (float)height, 0.1f, 100.0f);
    glm::mat4 view = camera.GetViewMatrix();

    ssao->Compute(gBuffer->gPosition, gBuffer->gNormal, projection, view);
    ssao->Blur();

    // 2. Lighting Pass
    postProcessor->BeginRender(); // bind HDR FBO

    lightingShader->use();
    glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, gBuffer->gPosition);
    glActiveTexture(GL_TEXTURE1); glBindTexture(GL_TEXTURE_2D, gBuffer->gNormal);
    glActiveTexture(GL_TEXTURE2); glBindTexture(GL_TEXTURE_2D, gBuffer->gAlbedoSpec);
    glActiveTexture(GL_TEXTURE3); glBindTexture(GL_TEXTURE_2D, ssao->GetSSAOTexture());

    glActiveTexture(GL_TEXTURE4);
    glBindTexture(GL_TEXTURE_2D, gBuffer->gEmission);

    lightingShader->setVec3("viewPos", camera.Position);
    lightingShader->setFloat("uTime", glfwGetTime());
}

unsigned int DeferredRenderer::loadTexture(char const* path) {
    unsigned int textureID;
    glGenTextures(1, &textureID);

    int width, height, nrComponents;
    unsigned char* data = stbi_load(path, &width, &height, &nrComponents, 0);
    if (data) {
        GLenum format;
        if (nrComponents == 1) format = GL_RED;
        else if (nrComponents == 3) format = GL_RGB;
        else if (nrComponents == 4) format = GL_RGBA;

        glBindTexture(GL_TEXTURE_2D, textureID);
        glTexImage2D(GL_TEXTURE_2D, 0, format, width, height, 0, format, GL_UNSIGNED_BYTE, data);
        glGenerateMipmap(GL_TEXTURE_2D);

        // �k�u�K�Ϥ@�w�n�� Repeat
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        // �Y�p�ɨϥΤT�u�ʹL�o�A�קK�{�{
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

        stbi_image_free(data);
    }
    else {
        std::cout << "Texture failed to load at path: " << path << std::endl;
        stbi_image_free(data);
    }
    return textureID;
}

void DeferredRenderer::EndLightingPass() {
    Primitives::renderQuad();
}

void DeferredRenderer::BeginForwardPass(Camera& camera) {
    // copy GBuffer -> HDR FBO)
    glBindFramebuffer(GL_READ_FRAMEBUFFER, gBuffer->gBuffer);
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, postProcessor->hdrFBO);
    glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_DEPTH_BUFFER_BIT, GL_NEAREST);

    glBindFramebuffer(GL_FRAMEBUFFER, postProcessor->hdrFBO);

    lightBoxShader->use();
    glm::mat4 projection = glm::perspective(glm::radians(camera.Zoom), (float)width / (float)height, 0.1f, 100.0f);
    glm::mat4 view = camera.GetViewMatrix();
    lightBoxShader->setMat4("projection", glm::value_ptr(projection));
    lightBoxShader->setMat4("view", glm::value_ptr(view));
}

void DeferredRenderer::EndForwardPass() {
    postProcessor->EndRender(); // unbind FBO
}

void DeferredRenderer::RenderPostProcess() {
    postProcessor->RenderBloom();
    postProcessor->RenderFinal(1.0f);
}