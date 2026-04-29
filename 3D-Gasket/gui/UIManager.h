#pragma once
#include <GLFW/glfw3.h>

class UIManager
{
public:
    void init(GLFWwindow* window);
    void beginFrame();
    void endFrame();
    void cleanup();

    void drawContextMenu(int& subdivisionLevel);
};