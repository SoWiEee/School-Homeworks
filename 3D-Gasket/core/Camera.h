#pragma once

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>

class Camera {
public:
    Camera();

    // 設定攝影機位置和朝向
    void setPosition(const glm::vec3& pos);
    void setTarget(const glm::vec3& target);

    // 取得 View 和 Projection 矩陣
    glm::mat4 getViewMatrix() const;
    glm::mat4 getProjectionMatrix(float aspectRatio) const;

private:
    // 攝影機狀態
    glm::vec3 Position;
    glm::vec3 Target;
    glm::vec3 Up; // 我們假設永遠是 (0, 1, 0)
    float OrthoSize;

    // 投影參數
    float Fov;  // 視野 (Field of View)
    float Near; // 近平面
    float Far;  // 遠平面
};