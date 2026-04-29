#include "Camera.h"

Camera::Camera()
    : Position(0.0f, 0.0f, 3.0f),  // 預設位置
    Target(0.0f, 0.0f, 0.0f),      // 預設看向原點
    Up(0.0f, 1.0f, 0.0f),          // 預設 Y 軸向上
    Fov(45.0f),                    // 預設 45 度視野
    Near(0.1f),
    Far(100.0f),
    OrthoSize(0.6f)
{
}

void Camera::setPosition(const glm::vec3& pos) {
    Position = pos;
}

void Camera::setTarget(const glm::vec3& target) {
    Target = target;
}

glm::mat4 Camera::getViewMatrix() const {
    return glm::lookAt(Position, Target, Up);
}

glm::mat4 Camera::getProjectionMatrix(float aspectRatio) const {
    float top = OrthoSize;
    float bottom = -OrthoSize;
    float right = OrthoSize * aspectRatio;
    float left = -right;

    return glm::ortho(left, right, bottom, top, Near, Far);
    // return glm::perspective(glm::radians(Fov), aspectRatio, Near, Far);
}