#include "TetraGasket.h"

static const glm::vec3 baseVertices[4] = {
    glm::vec3(0.0f, 0.0f, sqrt(6.0f) / 4.0f),                   // v[0]
    glm::vec3(0.0f, sqrt(3.0f) / 3.0f, sqrt(6.0f) / 12.0f),     // v[1]
    glm::vec3(-0.5f, -sqrt(3.0f) / 6.0, sqrt(6.0f) / 12.0f),    // v[2]
    glm::vec3(0.5f, -sqrt(3.0f) / 6.0, sqrt(6.0f) / 12.0f)      // v[3]
};

static const glm::vec3 faceColors[4] = {
    glm::vec3(1.0f, 0.0f, 0.0f), // Red
    glm::vec3(0.0, 1.0, 0.0),    // Green
    glm::vec3(0.0f, 0.0f, 1.0f), // Blue
    glm::vec3(0.0f, 0.0f, 0.0f)  // Black
};

void TetraGasket::init() {
    glCreateVertexArrays(1, &VAO);
    glCreateBuffers(1, &VBO_Position);
    glCreateBuffers(1, &VBO_Color);

    // Position (Loc 0)
    glEnableVertexArrayAttrib(VAO, 0);
    glVertexArrayAttribFormat(VAO, 0, 3, GL_FLOAT, GL_FALSE, 0);
    glVertexArrayAttribBinding(VAO, 0, 0);

    // Color (Loc 1)
    glEnableVertexArrayAttrib(VAO, 1);
    glVertexArrayAttribFormat(VAO, 1, 3, GL_FLOAT, GL_FALSE, 0);
    glVertexArrayAttribBinding(VAO, 1, 1);

	// Bind VBOs to VAO
    glVertexArrayVertexBuffer(VAO, 0, VBO_Position, 0, sizeof(glm::vec3));
    glVertexArrayVertexBuffer(VAO, 1, VBO_Color, 0, sizeof(glm::vec3));
}

void TetraGasket::generate(int level) {
    Positions.clear();
    Colors.clear();

    dividePyramid(baseVertices[0], baseVertices[1], baseVertices[2], baseVertices[3], level);

    VertexCount = Positions.size();

    if (VertexCount > 0) {
        glNamedBufferData(VBO_Position, VertexCount * sizeof(glm::vec3), Positions.data(), GL_DYNAMIC_DRAW);
        glNamedBufferData(VBO_Color, VertexCount * sizeof(glm::vec3), Colors.data(), GL_DYNAMIC_DRAW);
    }
}

void TetraGasket::dividePyramid(const glm::vec3& v1, const glm::vec3& v2, const glm::vec3& v3, const glm::vec3& v4, int level) {
    if (level == 0) {
        drawTetra(v1, v2, v3, v4);
    } else {
		// calculate midpoints of each edge
        glm::vec3 m12 = 0.5f * (v1 + v2);
        glm::vec3 m13 = 0.5f * (v1 + v3);
        glm::vec3 m14 = 0.5f * (v1 + v4);
        glm::vec3 m23 = 0.5f * (v2 + v3);
        glm::vec3 m24 = 0.5f * (v2 + v4);
        glm::vec3 m34 = 0.5f * (v3 + v4);

        dividePyramid(v1, m12, m13, m14, level - 1);
        dividePyramid(m12, v2, m23, m24, level - 1);
        dividePyramid(m13, m23, v3, m34, level - 1);
        dividePyramid(m14, m24, m34, v4, level - 1);
    }
}

void TetraGasket::drawTetra(const glm::vec3& v1, const glm::vec3& v2, const glm::vec3& v3, const glm::vec3& v4) {
    addTriangle(v1, v2, v3, faceColors[0]); // Red
    addTriangle(v4, v3, v2, faceColors[3]); // Black
    addTriangle(v1, v4, v2, faceColors[2]); // Blue
    addTriangle(v1, v3, v4, faceColors[1]); // Green
}

void TetraGasket::addTriangle(const glm::vec3& p1, const glm::vec3& p2, const glm::vec3& p3, const glm::vec3& color) {
    Positions.push_back(p1);
    Positions.push_back(p2);
    Positions.push_back(p3);

    Colors.push_back(color);
    Colors.push_back(color);
    Colors.push_back(color);
}

void TetraGasket::draw() {
    if (VertexCount > 0) {
        glBindVertexArray(VAO);
        glDrawArrays(GL_TRIANGLES, 0, static_cast<GLsizei>(VertexCount));
        glBindVertexArray(0);
    }
}

void TetraGasket::cleanup() {
    if (VBO_Color != 0) glDeleteBuffers(1, &VBO_Color);
    if (VBO_Position != 0) glDeleteBuffers(1, &VBO_Position);
    if (VAO != 0) glDeleteVertexArrays(1, &VAO);
}