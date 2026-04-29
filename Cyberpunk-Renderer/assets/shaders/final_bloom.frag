#version 450 core
out vec4 FragColor;
in vec2 TexCoords;

uniform sampler2D scene;      // HDR Scene
uniform sampler2D bloomBlur;  // blurreds bloom
uniform float exposure;

void main()
{             
    vec3 hdrColor = texture(scene, TexCoords).rgb;      
    vec3 bloomColor = texture(bloomBlur, TexCoords).rgb;
    
    // Additive Blending
    hdrColor += bloomColor;

    // Tone Mapping
    vec3 result = vec3(1.0) - exp(-hdrColor * exposure);
    
    // Gamma Correction
    const float gamma = 2.2;
    result = pow(result, vec3(1.0 / gamma));

    FragColor = vec4(result, 1.0);
}