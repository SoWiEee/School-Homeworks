#version 450 core

layout (location = 0) out vec4 gPosition; 
layout (location = 1) out vec3 gNormal;
layout (location = 2) out vec4 gAlbedoSpec;
layout (location = 3) out vec3 gEmission;

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoords;

uniform vec3 objectColor;
uniform sampler2D normalMap;

float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}

vec3 getTriplanarNormal(vec3 worldPos, vec3 worldNormal, float scale) {
    // blending weight
    vec3 blend = abs(worldNormal);
    blend = pow(blend, vec3(4.0)); 
    blend /= (blend.x + blend.y + blend.z); 

    // projection surface uv
    vec2 uvX = worldPos.zy * scale;
    vec2 uvY = worldPos.xz * scale;
    vec2 uvZ = worldPos.xy * scale;

    // load normal map
    vec3 tnormalX = texture(normalMap, uvX).rgb * 2.0 - 1.0;
    vec3 tnormalY = texture(normalMap, uvY).rgb * 2.0 - 1.0;
    vec3 tnormalZ = texture(normalMap, uvZ).rgb * 2.0 - 1.0;

    // tangent space -> world space
    
    vec3 axisSign = sign(worldNormal);
    
    tnormalX.z *= axisSign.x; 
    vec3 worldNormalX = vec3(tnormalX.z, tnormalX.y, tnormalX.x); // Swizzle: ZYX
    tnormalY.z *= axisSign.y;
    vec3 worldNormalY = vec3(tnormalY.x, tnormalY.z, tnormalY.y); // Swizzle: XZY
    tnormalZ.z *= axisSign.z;
    vec3 worldNormalZ = vec3(tnormalZ.x, tnormalZ.y, tnormalZ.z); // Swizzle: XYZ
    
    // blending nromal
    vec3 finalNormal = normalize(
        worldNormalX * blend.x + 
        worldNormalY * blend.y + 
        worldNormalZ * blend.z
    );

    return finalNormal;
}

void main()
{    
    gPosition = vec4(FragPos, 1.0);
    vec3 geometricNormal = normalize(Normal);
    vec3 detailedNormal = getTriplanarNormal(FragPos, geometricNormal, 1.0);
    gNormal = detailedNormal;
    
    vec3 baseColor = vec3(0.05, 0.05, 0.07);    // gray
    gAlbedoSpec.rgb = baseColor;
    gAlbedoSpec.a = 0.8;

    // Procedural Windows
    
    vec2 windowUV;
    if (abs(Normal.y) > 0.9) {
        windowUV = FragPos.xz;
    } else if (abs(Normal.x) > 0.9) {
        windowUV = FragPos.zy;
    } else {
        windowUV = FragPos.xy;
    }

    // tiling
    vec2 tilePos = windowUV * 2.0; 
    vec2 tileIndex = floor(tilePos);
    vec2 tileUV = fract(tilePos);

    // draw window
    float padding = 0.15;
    float windowMask = step(padding, tileUV.x) * step(padding, tileUV.y) * step(tileUV.x, 1.0 - padding) * step(tileUV.y, 1.0 - padding);

    // random noise
    float noise = random(tileIndex);
    vec3 emitColor = vec3(0.0);

    // ignore floor
    if (abs(Normal.y) < 0.9 && windowMask > 0.5) {
        if (noise > 0.7) {
            emitColor = vec3(0.5, 0.8, 1.0) * 3.0;  // bloom
        } else if (noise > 0.65) {
            emitColor = vec3(1.0, 0.6, 0.2) * 3.0;
        } else {
            gAlbedoSpec.rgb = vec3(0.1, 0.1, 0.15);
        }
    }
    gEmission = emitColor;
}