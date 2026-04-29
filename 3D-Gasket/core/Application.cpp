#include "Application.h"
#include "../gui/UIManager.h"

#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <iostream>
#include <stdexcept>
#include <string>

// --- Application Public ---

void Application::run() {
    try {
        init();
        mainLoop();
        cleanup();
    }
    catch (const std::exception& e) {
        std::cerr << "An unrecoverable error occurred: " << e.what() << std::endl;
        if (window) {
            glfwDestroyWindow(window);
        }
        glfwTerminate();
    }
}

// --- Application Private ---

void Application::init() {
    if (!glfwInit()) {
        throw std::runtime_error("Failed to initialize GLFW");
    }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 5);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    glfwWindowHint(GLFW_SAMPLES, 16); // 16x MSAA

    std::string windowTitle = "S11259043";
    window = glfwCreateWindow(windowWidth, windowHeight, windowTitle.c_str(), NULL, NULL);
    if (!window) {
        glfwTerminate();
        throw std::runtime_error("Failed to create GLFW window");
    }

    glfwMakeContextCurrent(window);
    glfwSetWindowUserPointer(window, this);

    // set callbacks
    glfwSetKeyCallback(window, keyCallback);
    glfwSetFramebufferSizeCallback(window, framebufferSizeCallback);

    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        throw std::runtime_error("Failed to initialize GLAD");
    }

	glEnable(GL_MULTISAMPLE);   // enable MSAA

    glViewport(0, 0, windowWidth, windowHeight);
    glEnable(GL_DEPTH_TEST); // z-buffer
	glEnable(GL_CULL_FACE);  // cull back-face

    gui.init(window);

    try {
        shader.load("shader/gasket.vert", "shader/gasket.frag");
    }
    catch (const std::exception& e) {
        throw std::runtime_error(std::string("Shader load error: ") + e.what());
    }

    gasket.init();

    // Z=2 -> (0,0,0)
    cam.setPosition(glm::vec3(0.0f, 0.0f, 2.0f));
    cam.setTarget(glm::vec3(0.0f, 0.0f, 0.0f));

    // init state
    SubdivisionLevel = 0;
    LevelChanged = true;
}

void Application::mainLoop() {
    while (!glfwWindowShouldClose(window)) {
		// unput handling
        glfwPollEvents();

        gui.beginFrame();

        // draw UI
        int previousLevel = SubdivisionLevel;
        gui.drawContextMenu(SubdivisionLevel);

        // Level changed
        if (SubdivisionLevel != previousLevel) {
            LevelChanged = true;
        }

        // Geometry update
        if (LevelChanged) {
            gasket.generate(SubdivisionLevel);
            LevelChanged = false; // reset flag
        }

        // Rendering
        glClearColor(1.0f, 1.0f, 1.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        shader.use();

        // MVP
        glm::mat4 projection = cam.getProjectionMatrix((float)windowWidth / (float)windowHeight);
        glm::mat4 view = cam.getViewMatrix();
        glm::mat4 model = glm::mat4(1.0f); // ³æ¦ì¯x°}

        shader.setMat4("MVP", projection * view * model);

        // draw 3D gasket
        gasket.draw();

        // draw ImGui
        gui.endFrame();

        glfwSwapBuffers(window);
    }
}

void Application::cleanup()
{
    gui.cleanup();
    gasket.cleanup();
    shader.cleanup();

    if (window) {
        glfwDestroyWindow(window);
    }
    glfwTerminate();
}

// Static Callbacks
void Application::keyCallback(GLFWwindow* window, int key, int scancode, int action, int mods)
{
    Application* app = static_cast<Application*>(glfwGetWindowUserPointer(window));
    if (!app) return;

    // 'q' or 'Q' to exit
    if ((key == GLFW_KEY_Q && action == GLFW_PRESS)) {
        glfwSetWindowShouldClose(window, true);
    }
}

void Application::framebufferSizeCallback(GLFWwindow* window, int width, int height)
{
    Application* app = static_cast<Application*>(glfwGetWindowUserPointer(window));
    if (app) {
        glViewport(0, 0, width, height);
        app->windowWidth = width;
        app->windowHeight = height;
    }
}