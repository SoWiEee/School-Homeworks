#pragma once
#include <glad/glad.h>
#include <glm/glm.hpp>
#include <vector>

class InstancedMesh {
public:
    unsigned int VAO, VBO, instanceVBO;
    int amount; // instance

    InstancedMesh(std::vector<glm::mat4>& models);
    ~InstancedMesh();

    void Draw();
};