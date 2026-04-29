#pragma once

#include <glad/glad.h>
#include <glm/glm.hpp>
#include <vector>

class TetraGasket {
public:
    void init();
    void generate(int level); // 產生 volume subdivision
    void draw();
    void cleanup();

private:
    // Volume Subdivision
    void dividePyramid(const glm::vec3& v1, const glm::vec3& v2, const glm::vec3& v3, const glm::vec3& v4, int level);

    // 在遞迴終點繪製一個完整的四面體
    void drawTetra(const glm::vec3& v1, const glm::vec3& v2, const glm::vec3& v3, const glm::vec3& v4);

    // 將單一三角形加入 vector
    void addTriangle(const glm::vec3& p1, const glm::vec3& p2, const glm::vec3& p3, const glm::vec3& color);

    GLuint VAO = 0;
    GLuint VBO_Position = 0;
    GLuint VBO_Color = 0;

    std::vector<glm::vec3> Positions;
    std::vector<glm::vec3> Colors;

    size_t VertexCount = 0;
};