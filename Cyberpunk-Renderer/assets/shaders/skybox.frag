#version 450 core
layout (location = 0) out vec4 FragColor;
layout (location = 1) out vec4 BrightColor;

in vec3 TexCoords;

uniform samplerCube skybox;

void main()
{    
    vec3 color = texture(skybox, TexCoords).rgb;
    
    // 讓天空稍微暗一點
    color *= 0.5; 

    FragColor = vec4(color, 1.0);
    
    float brightness = dot(color, vec3(0.2126, 0.7152, 0.0722));
    if(brightness > 1.0)
        BrightColor = vec4(color, 1.0);
    else
        BrightColor = vec4(0.0, 0.0, 0.0, 1.0);
}