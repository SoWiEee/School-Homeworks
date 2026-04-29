#pragma once

#include <glad/glad.h>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>

#include <vector>

enum Camera_Movement {
    FORWARD,
    BACKWARD,
    LEFT,
    RIGHT,
    UP,
    DOWN
};

const float YAW = -90.0f; // 預設看向 -Z 軸
const float PITCH = 0.0f;
const float SPEED = 50.0f; // 地形很大，速度設快一點
const float SENSITIVITY = 0.1f;
const float ZOOM = 45.0f;

class Camera
{
public:
    // --- 相機屬性 (Vectors) ---
    glm::vec3 Position;
    glm::vec3 Front;
    glm::vec3 Up;
    glm::vec3 Right;
    glm::vec3 WorldUp;

    // --- 歐拉角 (Euler Angles) ---
    float Yaw;
    float Pitch;

    // --- 相機選項 ---
    float MovementSpeed;
    float MouseSensitivity;
    float Zoom; // 控制 FOV

    Camera(glm::vec3 position = glm::vec3(0.0f, 0.0f, 0.0f), glm::vec3 up = glm::vec3(0.0f, 1.0f, 0.0f), float yaw = YAW, float pitch = PITCH);
    Camera(float posX, float posY, float posZ, float upX, float upY, float upZ, float yaw, float pitch);

    // 回傳 View Matrix (最重要的函數，給 Shader 用)
    glm::mat4 GetViewMatrix();

    // 處理鍵盤移動 (WASD)
    void ProcessKeyboard(Camera_Movement direction, float deltaTime);

    // 處理滑鼠視角轉動
    void ProcessMouseMovement(float xoffset, float yoffset, GLboolean constrainPitch = true);

    // 處理滾輪縮放 (FOV)
    void ProcessMouseScroll(float yoffset);

private:
    void updateCameraVectors();
};