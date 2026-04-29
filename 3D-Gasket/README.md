# 3D Gasket: OpenGL Volume Subdivision

[![Language](https://img.shields.io/badge/Language-C%2B%2B-blue.svg)](https://isocpp.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An implementation of a 3D Gasket (Sierpinski Tetrahedron) for a university computer graphics course. This project uses a modern OpenGL 4.5 pipeline to render a 3D fractal with true **Volume Subdivision**.

The application is built in C++ using a modular, object-oriented design and features an interactive UI powered by **Dear ImGui** for real-time control.

![Screenshot of 3D Gasket at Level 3](https://i.imgur.com/example.png)
*(Please replace this with a real screenshot of your project)*

---

## Features

* **Modern OpenGL 4.5:** Uses a Core Profile with VAOs, VBOs, and GLSL shaders. Avoids all legacy (Immediate Mode) functions.
* **True Volume Subdivision:** Implements a recursive `dividePyramid` algorithm that generates 4 new 3D tetrahedrons from each parent, correctly "removing" the central octahedron. This ensures that every resulting fractal component is a 3D object, not a 2D surface.
* **Interactive UI:** Features a right-click context menu (built with Dear ImGui) to change the subdivision level (0-3) in real-time.
* **Modular C++ Design:** Code is organized into classes (`Application`, `TetraGasket`, `UIManager`, `Shader`, `Camera`) for clarity, maintainability, and extensibility.
* **Direct State Access (DSA):** Utilizes `glNamedBufferData` for more efficient, object-oriented buffer management.

## Technical Stack

* **C++17**
* **OpenGL 4.5 (Core Profile)**
* **GLAD:** To load OpenGL function pointers.
* **GLFW:** For windowing, context creation, and input.
* **GLM:** For all vector (`glm::vec3`) and matrix (`glm::mat4`) mathematics.
* **Dear ImGui:** For the right-click context menu.

## Getting Started

This project is built using CMake, which is the recommended way to compile it.

### Prerequisites

* A C++17 compliant compiler (e.g., MSVC, GCC, Clang)
* **CMake** (3.15 or higher)
* **GLFW**
* The **GLAD**, **GLM**, and **Dear ImGui** libraries (this project assumes they are included in a `libs/` directory or found as system packages).

### Build Instructions

1.  Clone the repository (and its submodules, if you are using them for dependencies):
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    # If using submodules for libs:
    # git submodule update --init --recursive
    ```

2.  Configure and build with CMake:
    ```bash
    mkdir build
    cd build
    cmake ..
    cmake --build .
    ```
    *On Windows with Visual Studio, you may want to specify the config:*
    ```bash
    cmake --build . --config Release
    ```

3.  Run the executable:
    ```bash
    # On Windows
    ./Release/3D_Gasket.exe
    # On Linux/macOS
    ./3D_Gasket
    ```
    *(Note: The executable name `3D_Gasket` may vary based on your `CMakeLists.txt` `project()` name.)*

## How to Use

* **Right-Click:** Opens the context menu.
* **Menu > Subdivision Level:** Select `0`, `1`, `2`, or `3` to change the recursion depth of the fractal.
* **Menu > Exit:** Quits the application.
* **Keyboard 'q' / 'Q':** Quits the application.

## Core Algorithm: Volume Subdivision

The core logic resides in the `TetraGasket::dividePyramid` function. Unlike *Surface Subdivision* (which applies a 2D fractal to each flat face), *Volume Subdivision* recursively divides the 3D space.

The algorithm can be described as follows:

```cpp
void dividePyramid(v1, v2, v3, v4, level)
{
    // 1. Base Case: If level is 0, we have reached the
    //    maximum depth. We draw the current tetrahedron.
    if (level == 0)
    {
        drawTetra(v1, v2, v3, v4);
    }
    // 2. Recursive Step:
    else
    {
        // a. Find the 6 midpoints of the tetrahedron's edges
        m12 = midpoint(v1, v2);
        m13 = midpoint(v1, v3);
        m14 = midpoint(v1, v4);
        m23 = midpoint(v2, v3);
        m24 = midpoint(v2, v4);
        m34 = midpoint(v3, v4);

        // b. Recurse on the 4 smaller tetrahedrons
        //    located at the corners of the parent.
        dividePyramid(v1, m12, m13, m14, level - 1);
        dividePyramid(m12, v2, m23, m24, level - 1);
        dividePyramid(m13, m23, v3, m34, level - 1);
        dividePyramid(m14, m24, m34, v4, level - 1);
        
        // c. The central octahedron (formed by the 6 midpoints)
        //    is implicitly "removed" by simply not being
        //    drawn or recursed upon.
    }
}
