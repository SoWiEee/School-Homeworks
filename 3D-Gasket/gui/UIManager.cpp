#include "UIManager.h"
#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

void UIManager::init(GLFWwindow* window) {
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    ImFontConfig cfg;
    cfg.SizePixels = 22.0f; // Set desired font size in pixels
    io.Fonts->AddFontFromFileTTF("Roboto-Medium.ttf", 22.0f, &cfg);
    ImGui::StyleColorsDark();   // dark theme

    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init("#version 450");
}

void UIManager::beginFrame() {
    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();
}

void UIManager::endFrame() {
    ImGui::Render();
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
}

void UIManager::drawContextMenu(int& subdivisionLevel) {

    ImGuiIO& io = ImGui::GetIO();
    ImGui::SetNextWindowPos(ImVec2(0.0f, 0.0f));
    ImGui::SetNextWindowSize(io.DisplaySize);

    ImGuiWindowFlags window_flags = 0;
    window_flags |= ImGuiWindowFlags_NoTitleBar;
    window_flags |= ImGuiWindowFlags_NoResize;
    window_flags |= ImGuiWindowFlags_NoMove;
    window_flags |= ImGuiWindowFlags_NoScrollbar;
    window_flags |= ImGuiWindowFlags_NoCollapse;
    window_flags |= ImGuiWindowFlags_NoSavedSettings;
    window_flags |= ImGuiWindowFlags_NoBackground;
    window_flags |= ImGuiWindowFlags_NoBringToFrontOnFocus;

    ImGui::Begin("MainCanvas", NULL, window_flags);

	// detect right-click
    if (ImGui::BeginPopupContextWindow("main_context_popup"))
    {
        // Item - Subdivision Level
        if (ImGui::BeginMenu("Subdivision Level"))
        {
            if (ImGui::MenuItem("0", NULL, subdivisionLevel == 0)) { subdivisionLevel = 0; }
            if (ImGui::MenuItem("1", NULL, subdivisionLevel == 1)) { subdivisionLevel = 1; }
            if (ImGui::MenuItem("2", NULL, subdivisionLevel == 2)) { subdivisionLevel = 2; }
            if (ImGui::MenuItem("3", NULL, subdivisionLevel == 3)) { subdivisionLevel = 3; }

            ImGui::EndMenu();
        }

        ImGui::Separator();

        // Item - Exit
        if (ImGui::MenuItem("Exit"))
        {
            GLFWwindow* window = glfwGetCurrentContext();
            glfwSetWindowShouldClose(window, true);
        }

        ImGui::EndPopup();
    }

    ImGui::End();
}

void UIManager::cleanup() {
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
}