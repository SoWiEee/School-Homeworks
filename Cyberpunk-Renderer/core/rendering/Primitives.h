#pragma once
#include <glad/glad.h>

class Primitives {
public:
    static void renderCube();
    static void renderQuad();
private:
    static unsigned int cubeVAO, cubeVBO;
    static unsigned int quadVAO, quadVBO;
};