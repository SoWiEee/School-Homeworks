#pragma once
#include <glad/glad.h>
#include <string>

class Texture {
public:
    unsigned int ID;
    int width, height, nrChannels;

    Texture(const char* path);
    ~Texture();
    void bind(int unit = 0); // 綁定到指定的 Texture Unit
};