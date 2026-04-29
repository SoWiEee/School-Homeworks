#pragma once
#include <glad/glad.h>
#include <vector>
#include <string>
#include <iostream>
#include "../Shader.h"
#include "../Camera.h"
#include "../Texture.h"
#include "stb_image.h"
#include <glm/gtc/type_ptr.hpp>

class SkyboxRenderer {
public:
    unsigned int skyboxVAO, skyboxVBO;
    unsigned int cubemapTexture;
    Shader* skyboxShader;

    SkyboxRenderer();
    ~SkyboxRenderer();
    void Draw(Camera& camera);

private:
    unsigned int loadCubemap(std::vector<std::string> faces);
};