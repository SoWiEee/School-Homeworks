#pragma once

#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include "Camera.h"
#include "Shader.h"
#include "../rendering/TetraGasket.h"
#include "../gui/UIManager.h"

class Application {
public:
    void run();

private:
    void init();
    void mainLoop();
    void cleanup();

    // static Callbacks
    static void keyCallback(GLFWwindow* window, int key, int scancode, int action, int mods);
    static void framebufferSizeCallback(GLFWwindow* window, int width, int height);

    GLFWwindow* window = nullptr;
    UIManager gui;
    Camera cam;
    Shader shader;
    TetraGasket gasket;

    // 狀態
    int windowWidth = 1280;
    int windowHeight = 720;
    int SubdivisionLevel = 0; // 初始 subdivision level = 0
    bool LevelChanged = true; // 標記 level 是否改變，以便重新產生
};