#include "Shader.h"

Shader::Shader(const char* vertexPath, const char* fragmentPath, const char* tcsPath, const char* tesPath)
{
    // 1. 從檔案路徑讀取原始碼
    std::string vertexCode, fragmentCode, tcsCode, tesCode;
    std::ifstream vShaderFile, fShaderFile, tcsShaderFile, tesShaderFile;

    // 確保 ifstream 物件可以拋出例外
    vShaderFile.exceptions(std::ifstream::failbit | std::ifstream::badbit);
    fShaderFile.exceptions(std::ifstream::failbit | std::ifstream::badbit);
    tcsShaderFile.exceptions(std::ifstream::failbit | std::ifstream::badbit);
    tesShaderFile.exceptions(std::ifstream::failbit | std::ifstream::badbit);

    try {
        // 開啟檔案
        vShaderFile.open(vertexPath);
        fShaderFile.open(fragmentPath);
        std::stringstream vShaderStream, fShaderStream;

        vShaderStream << vShaderFile.rdbuf();
        fShaderStream << fShaderFile.rdbuf();

        vShaderFile.close();
        fShaderFile.close();

        vertexCode = vShaderStream.str();
        fragmentCode = fShaderStream.str();

        // 讀取 Tessellation Shaders (如果有傳入路徑)
        if (tcsPath != nullptr && tesPath != nullptr) {
            tcsShaderFile.open(tcsPath);
            tesShaderFile.open(tesPath);
            std::stringstream tcsShaderStream, tesShaderStream;
            tcsShaderStream << tcsShaderFile.rdbuf();
            tesShaderStream << tesShaderFile.rdbuf();
            tcsShaderFile.close();
            tesShaderFile.close();
            tcsCode = tcsShaderStream.str();
            tesCode = tesShaderStream.str();
        }
    }
    catch (std::ifstream::failure& e) {
        std::cout << "ERROR::SHADER::FILE_NOT_SUCCESFULLY_READ" << std::endl;
    }

    const char* vShaderCode = vertexCode.c_str();
    const char* fShaderCode = fragmentCode.c_str();

    // 2. 編譯 Shaders
    unsigned int vertex, fragment, tcs, tes;

    // Vertex Shader
    vertex = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertex, 1, &vShaderCode, NULL);
    glCompileShader(vertex);
    checkCompileErrors(vertex, "VERTEX");

    // Fragment Shader
    fragment = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragment, 1, &fShaderCode, NULL);
    glCompileShader(fragment);
    checkCompileErrors(fragment, "FRAGMENT");

    // Tessellation Shaders
    if (tcsPath != nullptr && tesPath != nullptr) {
        const char* tcsShaderCode = tcsCode.c_str();
        const char* tesShaderCode = tesCode.c_str();

        tcs = glCreateShader(GL_TESS_CONTROL_SHADER);
        glShaderSource(tcs, 1, &tcsShaderCode, NULL);
        glCompileShader(tcs);
        checkCompileErrors(tcs, "TESS_CONTROL");

        tes = glCreateShader(GL_TESS_EVALUATION_SHADER);
        glShaderSource(tes, 1, &tesShaderCode, NULL);
        glCompileShader(tes);
        checkCompileErrors(tes, "TESS_EVALUATION");
    }

    // 3. Shader Program
    ID = glCreateProgram();
    glAttachShader(ID, vertex);
    glAttachShader(ID, fragment);
    if (tcsPath != nullptr) {
        glAttachShader(ID, tcs);
        glAttachShader(ID, tes);
    }
    glLinkProgram(ID);
    checkCompileErrors(ID, "PROGRAM");

    glDeleteShader(vertex);
    glDeleteShader(fragment);
    if (tcsPath != nullptr) {
        glDeleteShader(tcs);
        glDeleteShader(tes);
    }
}

void Shader::use() { glUseProgram(ID); }
void Shader::setBool(const std::string& name, bool value) const { glUniform1i(glGetUniformLocation(ID, name.c_str()), (int)value); }
void Shader::setInt(const std::string& name, int value) const { glUniform1i(glGetUniformLocation(ID, name.c_str()), value); }
void Shader::setFloat(const std::string& name, float value) const { glUniform1f(glGetUniformLocation(ID, name.c_str()), value); }
void Shader::setMat4(const std::string& name, const float* value) const { glUniformMatrix4fv(glGetUniformLocation(ID, name.c_str()), 1, GL_FALSE, value); }
void Shader::setVec3(const std::string& name, const glm::vec3& value) const {
    glProgramUniform3fv(ID, glGetUniformLocation(ID, name.c_str()), 1, &value[0]);
}
void Shader::setVec2(const std::string& name, const glm::vec2& value) const {
    glProgramUniform2fv(ID, glGetUniformLocation(ID, name.c_str()), 1, &value[0]);
}


void Shader::checkCompileErrors(unsigned int shader, std::string type)
{
    int success;
    char infoLog[1024];
    if (type != "PROGRAM") {
        glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
        if (!success) {
            glGetShaderInfoLog(shader, 1024, NULL, infoLog);
            std::cout << "ERROR::SHADER_COMPILATION_ERROR of type: " << type << "\n" << infoLog << "\n -- --------------------------------------------------- -- " << std::endl;
        }
    }
    else {
        glGetProgramiv(shader, GL_LINK_STATUS, &success);
        if (!success) {
            glGetProgramInfoLog(shader, 1024, NULL, infoLog);
            std::cout << "ERROR::PROGRAM_LINKING_ERROR of type: " << type << "\n" << infoLog << "\n -- --------------------------------------------------- -- " << std::endl;
        }
    }
}