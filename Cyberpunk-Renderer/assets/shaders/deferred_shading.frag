#version 450 core

layout (location = 0) out vec4 FragColor;
layout (location = 1) out vec4 BrightColor;

in vec2 TexCoords;

uniform sampler2D gPosition;
uniform sampler2D gNormal;
uniform sampler2D gAlbedoSpec;
uniform sampler2D ssao;
uniform sampler2D gEmission;

struct Light {
    vec3 Position;
    vec3 Color;
    float Linear;
    float Quadratic;
};

const int NR_LIGHTS = 100;
uniform Light lights[NR_LIGHTS];
uniform vec3 viewPos;

// volumetric fog params
const float FOG_DENSITY = 0.04;
const float FOG_HEIGHT_FALLOFF = 0.25;
const float FOG_HEIGHT_OFFSET = -1.0;

float ComputeFogIntegral(vec3 camPos, vec3 worldPos) {
    vec3 camToPoint = worldPos - camPos;
    float distance = length(camToPoint);
    float heightDiff = worldPos.y - camPos.y;
    
    if (abs(heightDiff) < 0.0001) heightDiff = 0.0001;

    float num = FOG_DENSITY * distance;
    float den = heightDiff * FOG_HEIGHT_FALLOFF;
    
    float valA = exp(-((camPos.y - FOG_HEIGHT_OFFSET) * FOG_HEIGHT_FALLOFF));
    float valB = exp(-((worldPos.y - FOG_HEIGHT_OFFSET) * FOG_HEIGHT_FALLOFF));
    
    float fogAmount = (num / den) * (valA - valB);
    return max(fogAmount, 0.0);
}

vec3 ComputeFogColor(vec3 viewDir, vec3 moonDir, vec3 baseFogColor) {
    float sunAmount = max(dot(viewDir, moonDir), 0.0);
    vec3 fogHighlightColor = vec3(0.6, 0.7, 0.9); 
    float scatterPower = pow(sunAmount, 8.0); 
    return mix(baseFogColor, fogHighlightColor, scatterPower * 0.5);
}

void main()
{
    vec3 FragPos = texture(gPosition, TexCoords).rgb;
    vec3 Normal = texture(gNormal, TexCoords).rgb;
    vec3 Diffuse = texture(gAlbedoSpec, TexCoords).rgb;
    float Specular = texture(gAlbedoSpec, TexCoords).a;
    vec3 Emission = texture(gEmission, TexCoords).rgb;
    
    float AmbientOcclusion = texture(ssao, TexCoords).r;

    bool isGeometry = length(Normal) > 0.1;

    float fragDist = length(FragPos - viewPos);
    if (!isGeometry) {
        fragDist = 1000.0; 
    }

    vec3 lighting = vec3(0.0);

    // calculate ambient/diffuse/specular
    if (isGeometry) {
        vec3 skyColor = vec3(0.05, 0.05, 0.15);
        vec3 groundColor = vec3(0.02, 0.02, 0.02);
        float hemiFactor = Normal.y * 0.5 + 0.5;
        vec3 ambientColor = mix(groundColor, skyColor, hemiFactor);
        
        vec3 ambient = ambientColor * Diffuse * AmbientOcclusion * 2.0;
        lighting = ambient;
    }

    vec3 viewDir = normalize(FragPos - viewPos); 
    vec3 volumetricFog = vec3(0.0);

    for(int i = 0; i < NR_LIGHTS; ++i)
    {
        float lightDist = length(lights[i].Position - viewPos);

        // suface illu
        if(isGeometry) {
            float distance = length(lights[i].Position - FragPos);
            if(distance < 15.0) { 
                vec3 lightDir = normalize(lights[i].Position - FragPos);
                vec3 diffuse = max(dot(Normal, lightDir), 0.0) * Diffuse * lights[i].Color;
                
                vec3 halfwayDir = normalize(lightDir + viewDir);  
                float spec = pow(max(dot(Normal, halfwayDir), 0.0), 16.0);
                vec3 specular = lights[i].Color * spec * Specular;
                
                float attenuation = 1.0 / (1.0 + lights[i].Linear * distance + lights[i].Quadratic * distance * distance);
                
                lighting += (diffuse + specular) * attenuation;
            }
        }

        // Volumetric Scattering
        if (lightDist < fragDist) 
        {
            vec3 lightToCamDir = normalize(lights[i].Position - viewPos);
            float cosTheta = dot(viewDir, lightToCamDir);
            
            if (cosTheta > 0.0) 
            {
                float haloFalloff = 100.0;
                float scattering = pow(cosTheta, haloFalloff);
                scattering *= 1.0 / (1.0 + lightDist * 0.2);
                volumetricFog += lights[i].Color * scattering * 1.0;
            }
        }
    }

    // moon lighting
    vec3 moonDir = normalize(vec3(0.5, 1.0, 0.3)); 
    if (isGeometry) {
        vec3 moonColor = vec3(0.05, 0.05, 0.15);       
        float diff = max(dot(Normal, moonDir), 0.0);
        vec3 moonDiffuse = diff * moonColor * Diffuse;
        
        vec3 halfwayDir = normalize(moonDir + viewDir);
        float spec = pow(max(dot(Normal, halfwayDir), 0.0), 32.0);
        vec3 moonSpecular = moonColor * spec * Specular; 

        lighting += moonDiffuse + moonSpecular;
        lighting += Emission;
    }

    lighting += volumetricFog; 

    // Global Volumetric Fog
    vec3 fogTargetPos = FragPos;
    if (!isGeometry) {
        fogTargetPos = viewPos + normalize(FragPos - viewPos) * 500.0;  // very far sky
    }

    float fogIntegral = ComputeFogIntegral(viewPos, fogTargetPos);
    float fogTransmittance = exp(-fogIntegral);

    vec3 baseFogColor = vec3(0.15, 0.05, 0.2); 
    vec3 finalFogColor = ComputeFogColor(viewDir, moonDir, baseFogColor);

    vec3 finalColor = mix(finalFogColor, lighting, fogTransmittance);

    FragColor = vec4(finalColor, 1.0);

    // Bloom
    float brightness = dot(finalColor, vec3(0.2126, 0.7152, 0.0722));
    float threshold = 2.0; 
    if(brightness > threshold)
        BrightColor = vec4(finalColor, 1.0);
    else
        BrightColor = vec4(0.0, 0.0, 0.0, 1.0);
}