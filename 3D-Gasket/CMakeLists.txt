cmake_minimum_required(VERSION 3.10)

project(Graphic-Homework VERSION 1.0 LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 1. set PATH
set(LIB_DIR "${CMAKE_SOURCE_DIR}/library")

set(GLAD_INCLUDE "${LIB_DIR}/glad/include")
set(GLAD_SRC     "${LIB_DIR}/glad/src/glad.c")

set(GLFW_INCLUDE "${LIB_DIR}/glfw/include")
set(GLFW_LIB_DIR "${LIB_DIR}/glfw/lib-vc2022")

set(GLM_INCLUDE  "${LIB_DIR}/glm")

set(IMGUI_DIR    "${LIB_DIR}/imgui")

# ImGui core file
file(GLOB IMGUI_SOURCES "${IMGUI_DIR}/*.cpp")

# ImGui Backends (GLFW + OpenGL3)
set(IMGUI_BACKENDS
    "${IMGUI_DIR}/backends/imgui_impl_glfw.cpp"
    "${IMGUI_DIR}/backends/imgui_impl_opengl3.cpp"
)

file(GLOB_RECURSE MY_SOURCE_FILES "core/*.cpp" "rendering/*.cpp" "gui/*.cpp")

# 3. define executable
add_executable(${PROJECT_NAME}
    src/main.cpp
    ${MY_SOURCE_FILES}
    ${GLAD_SRC}
    ${IMGUI_SOURCES}
    ${IMGUI_BACKENDS}
)

# 4. Include Directory
target_include_directories(${PROJECT_NAME} PRIVATE
    ${GLAD_INCLUDE}
    ${GLFW_INCLUDE}
    ${GLM_INCLUDE}
    ${IMGUI_DIR}
    "${IMGUI_DIR}/backends"
)

# 5. link Library
find_package(OpenGL REQUIRED)   # find OpenGL

# GLFW library for linking
target_link_directories(${PROJECT_NAME} PRIVATE ${GLFW_LIB_DIR})

# link library
target_link_libraries(${PROJECT_NAME} PRIVATE
    glfw3.lib
    OpenGL::GL
)

add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${CMAKE_SOURCE_DIR}/assets/shader"
        "$<TARGET_FILE_DIR:${PROJECT_NAME}>/assets/shader"
    COMMENT "Copying shaders to output directory..."
)