#pragma once
#include "../GBuffer.h"
#include "PostProcessor.h"
#include "../Shader.h"
#include "../Camera.h"
#include "SSAO.h"
#include <GLFW/glfw3.h>

class DeferredRenderer {
public:
    GBuffer* gBuffer;
    PostProcessor* postProcessor;

    Shader* gBufferShader;
    Shader* lightingShader;
    Shader* lightBoxShader;

    SSAO* ssao;

    int width, height;
    unsigned int buildingNormalMap;

    DeferredRenderer(int w, int h);
    ~DeferredRenderer();

    // �y�{���� API
    void BeginGeometryPass(Camera& camera);
    void EndGeometryPass();

    void BeginLightingPass(Camera& camera);
    void EndLightingPass();

    void BeginForwardPass(Camera& camera);
    void EndForwardPass();

    void RenderPostProcess(); // Bloom + Tone Mapping
    unsigned int loadTexture(char const* path);
};