#version 450 core
out float FragColor;

in vec2 TexCoords;

uniform sampler2D gPosition; // World Space
uniform sampler2D gNormal;   // World Space
uniform sampler2D texNoise;  // 4x4 Noise

uniform vec3 samples[64]; // Kernel
uniform mat4 projection;
uniform mat4 view;        // 用來轉 World -> View

// 參數 (可從 C++ 調整)
int kernelSize = 64;
float radius = 0.5; // 採樣半徑 (太小沒效果，太大會有雜訊)
float bias = 0.025; // 避免自我遮蔽的偏移量

void main()
{
    // 1. 讀取 G-Buffer 並轉換到 View Space
    vec3 worldPos = texture(gPosition, TexCoords).rgb;
    vec3 worldNormal = texture(gNormal, TexCoords).rgb;
    
    // ★ 關鍵：轉換到 View Space
    vec3 fragPos = vec3(view * vec4(worldPos, 1.0));
    vec3 normal = normalize(mat3(view) * worldNormal);

    // 2. 建立 TBN 矩陣 (讓採樣核隨機旋轉)
    // 螢幕解析度除以 4 (因為噪聲圖是 4x4)
    vec2 noiseScale = textureSize(gPosition, 0) / 4.0; 
    vec3 randomVec = texture(texNoise, TexCoords * noiseScale).xyz;
    
    vec3 tangent = normalize(randomVec - normal * dot(randomVec, normal));
    vec3 bitangent = cross(normal, tangent);
    mat3 TBN = mat3(tangent, bitangent, normal);

    // 3. 迭代計算遮蔽
    float occlusion = 0.0;
    for(int i = 0; i < kernelSize; ++i)
    {
        // 取得採樣點位置 (View Space)
        vec3 samplePos = TBN * samples[i]; 
        samplePos = fragPos + samplePos * radius; 
        
        // 投影到 Screen Space (取得 UV 座標)
        vec4 offset = vec4(samplePos, 1.0);
        offset = projection * offset; 
        offset.xyz /= offset.w; // Perspective Divide
        offset.xyz = offset.xyz * 0.5 + 0.5; // 變換到 0.0 - 1.0
        
        // 讀取該採樣點的實際深度 (從 G-Buffer)
        vec3 sampleWorldPos = texture(gPosition, offset.xy).rgb;
        float sampleDepth = (view * vec4(sampleWorldPos, 1.0)).z; // 轉到 View Space Z
        
        // 範圍檢查 (Range Check)：如果深度差太遠，就不應該互相遮蔽
        float rangeCheck = smoothstep(0.0, 1.0, radius / abs(fragPos.z - sampleDepth));
        
        // 如果採樣點比實際表面更深 (Z 值更小/更負)，代表被遮到了
        // 注意 View Space Z 通常是負的，越遠越小
        if (sampleDepth >= samplePos.z + bias)
            occlusion += 1.0 * rangeCheck;
    }
    
    occlusion = 1.0 - (occlusion / kernelSize);
    FragColor = occlusion;
}