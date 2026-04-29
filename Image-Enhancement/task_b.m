%[text] # Task B: 方法比較與權衡分析
%[text] 針對 P01（亮度）、P02（對比度）、P03（色彩）各比較兩種影像處理方法，量化 Mean/Std 變化並視覺化對比結果。使用 Image Processing Toolbox 內建函式。
%%
%[text] ## 建立輸出資料夾
if ~exist('output', 'dir'); mkdir('output'); end
if ~exist('output/task_b', 'dir'); mkdir('output/task_b'); end
%%
%[text] ## P01：Gamma 校正（γ=0.5）vs Global 直方圖等化
%[text] P01 為逆光場景，直方圖呈左偏雙峰。Gamma 校正（γ<1）非線性提亮暗部，高光衝擊小；Global HE 強制拉平整體分布，動態範圍均等化效果強。
img1   = imread('assets/P01.jpg');
gray1  = rgb2gray(img1);
m0_1   = mean(double(gray1(:)));
s0_1   = std(double(gray1(:)));
r0_1 = mean(double(img1(:,:,1)),'all');
g0_1 = mean(double(img1(:,:,2)),'all');
b0_1 = mean(double(img1(:,:,3)),'all');
% --- Method A: Gamma 校正 γ=0.5 ---
img1_ga  = uint8(255 * (double(img1)/255).^0.5);
gray1_ga = rgb2gray(img1_ga);
m_ga = mean(double(gray1_ga(:)));
s_ga = std(double(gray1_ga(:)));
r_ga = mean(double(img1_ga(:,:,1)),'all');
g_ga = mean(double(img1_ga(:,:,2)),'all');
b_ga = mean(double(img1_ga(:,:,3)),'all');
% --- Method B: Global HE（套用於 HSV V 通道，保留色相與飽和度）---
hsv1           = rgb2hsv(img1);
hsv1_he        = hsv1;
hsv1_he(:,:,3) = histeq(hsv1(:,:,3));
img1_he        = im2uint8(hsv2rgb(hsv1_he));
gray1_he       = rgb2gray(img1_he);
m_he = mean(double(gray1_he(:)));
s_he = std(double(gray1_he(:)));
r_he = mean(double(img1_he(:,:,1)),'all');
g_he = mean(double(img1_he(:,:,2)),'all');
b_he = mean(double(img1_he(:,:,3)),'all');
fprintf('=== P01 統計比較 ===\n');
fprintf('%-18s  Mean   Std    R      G      B     |R-B|\n', '方法');
fprintf('%-18s  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f\n', '原始',        m0_1,s0_1,r0_1,g0_1,b0_1,abs(r0_1-b0_1));
fprintf('%-18s  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f\n', 'Gamma γ=0.5', m_ga,s_ga,r_ga,g_ga,b_ga,abs(r_ga-b_ga));
fprintf('%-18s  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f\n', 'Global HE',   m_he,s_he,r_he,g_he,b_he,abs(r_he-b_he));
tiledlayout(2,3,'TileSpacing','compact','Padding','compact')
nexttile; imshow(img1);    title(sprintf('原始  M=%.0f S=%.0f',         m0_1, s0_1))
nexttile; imshow(img1_ga); title(sprintf('Gamma \\gamma=0.5  M=%.0f S=%.0f', m_ga,  s_ga))
nexttile; imshow(img1_he); title(sprintf('Global HE  M=%.0f S=%.0f',   m_he,  s_he))
nexttile; histogram(double(gray1(:)),   128,'BinLimits',[0,255]); xlabel('像素值'); ylabel('數量')
nexttile; histogram(double(gray1_ga(:)),128,'BinLimits',[0,255]); xlabel('像素值')
nexttile; histogram(double(gray1_he(:)),128,'BinLimits',[0,255]); xlabel('像素值')
saveas(gcf,'output/task_b/P01_comparison.png')
imwrite(img1_ga, 'output/task_b/b1-1.png')
imwrite(img1_he, 'output/task_b/b1-2.png')
%%
%[text] ## P02：Global HE vs CLAHE（對比度問題）
%[text] P02 整體偏暗且對比不足（Std=33.3）。Global HE 全域等化效果強但易放大雜訊；CLAHE 自適應分塊等化並限制對比放大倍率（ClipLimit=0.02），雜訊增幅受控。
img2   = imread('assets/P02.jpg');
gray2  = rgb2gray(img2);
m0_2   = mean(double(gray2(:)));
s0_2   = std(double(gray2(:)));
r0_2 = mean(double(img2(:,:,1)),'all');
g0_2 = mean(double(img2(:,:,2)),'all');
b0_2 = mean(double(img2(:,:,3)),'all');
% --- Method A: Global HE（套用於 HSV V 通道）---
hsv2            = rgb2hsv(img2);
hsv2_ghe        = hsv2;
hsv2_ghe(:,:,3) = histeq(hsv2(:,:,3));
img2_ghe        = im2uint8(hsv2rgb(hsv2_ghe));
gray2_ghe       = rgb2gray(img2_ghe);
m_ghe = mean(double(gray2_ghe(:)));
s_ghe = std(double(gray2_ghe(:)));
r_ghe = mean(double(img2_ghe(:,:,1)),'all');
g_ghe = mean(double(img2_ghe(:,:,2)),'all');
b_ghe = mean(double(img2_ghe(:,:,3)),'all');
% --- Method B: CLAHE（套用於 HSV V 通道，ClipLimit=0.02，8×8 tiles）---
hsv2_cl        = hsv2;
hsv2_cl(:,:,3) = adapthisteq(hsv2(:,:,3),'ClipLimit',0.02,'NumTiles',[8 8]);
img2_cl        = im2uint8(hsv2rgb(hsv2_cl));
gray2_cl       = rgb2gray(img2_cl);
m_cl = mean(double(gray2_cl(:)));
s_cl = std(double(gray2_cl(:)));
r_cl = mean(double(img2_cl(:,:,1)),'all');
g_cl = mean(double(img2_cl(:,:,2)),'all');
b_cl = mean(double(img2_cl(:,:,3)),'all');
fprintf('\n=== P02 統計比較 ===\n');
fprintf('%-18s  Mean   Std    R      G      B     |R-B|\n', '方法');
fprintf('%-18s  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f\n', '原始',      m0_2,s0_2,r0_2,g0_2,b0_2,abs(r0_2-b0_2));
fprintf('%-18s  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f\n', 'Global HE', m_ghe,s_ghe,r_ghe,g_ghe,b_ghe,abs(r_ghe-b_ghe));
fprintf('%-18s  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f\n', 'CLAHE',     m_cl,s_cl,r_cl,g_cl,b_cl,abs(r_cl-b_cl));
tiledlayout(2,3,'TileSpacing','compact','Padding','compact')
nexttile; imshow(img2);     title(sprintf('原始  M=%.0f S=%.0f',     m0_2,  s0_2))
nexttile; imshow(img2_ghe); title(sprintf('Global HE  M=%.0f S=%.0f', m_ghe, s_ghe))
nexttile; imshow(img2_cl);  title(sprintf('CLAHE  M=%.0f S=%.0f',     m_cl,  s_cl))
nexttile; histogram(double(gray2(:)),    128,'BinLimits',[0,255]); xlabel('像素值'); ylabel('數量')
nexttile; histogram(double(gray2_ghe(:)),128,'BinLimits',[0,255]); xlabel('像素值')
nexttile; histogram(double(gray2_cl(:)), 128,'BinLimits',[0,255]); xlabel('像素值')
saveas(gcf,'output/task_b/P02_comparison.png')
imwrite(img2_ghe, 'output/task_b/b2-1.png')
imwrite(img2_cl,  'output/task_b/b2-2.png')
%%
%[text] ## P03：RGB 灰世界校正 vs YCbCr 色調校正（色彩問題）
%[text] P03 偏暖（R=99.1，B=32.5，|R-B|=66.6）。RGB 灰世界假設場景均值應為中性灰，縮放各通道；YCbCr 在亮度不變的前提下將 Cb/Cr 通道平移至中立值（128），僅調整色度。
img3  = imread('assets/P03.jpg');
gray3 = rgb2gray(img3);
m0_3  = mean(double(gray3(:)));
s0_3  = std(double(gray3(:)));
r0 = mean(double(img3(:,:,1)),'all');
g0 = mean(double(img3(:,:,2)),'all');
b0 = mean(double(img3(:,:,3)),'all');
% --- Method A: RGB 灰世界校正 ---
ov_mean = (r0 + g0 + b0) / 3;
d3 = double(img3);
img3_gw        = d3;
img3_gw(:,:,1) = min(255, d3(:,:,1) * (ov_mean/r0));
img3_gw(:,:,2) = min(255, d3(:,:,2) * (ov_mean/g0));
img3_gw(:,:,3) = min(255, d3(:,:,3) * (ov_mean/b0));
img3_gw  = uint8(img3_gw);
gray3_gw = rgb2gray(img3_gw);
m_gw = mean(double(gray3_gw(:)));
s_gw = std(double(gray3_gw(:)));
r_gw = mean(double(img3_gw(:,:,1)),'all');
g_gw = mean(double(img3_gw(:,:,2)),'all');
b_gw = mean(double(img3_gw(:,:,3)),'all');
% --- Method B: YCbCr 色調校正（IPT rgb2ycbcr / ycbcr2rgb）---
ycc3  = rgb2ycbcr(img3);
ycc3d = double(ycc3);
cb_off = 128 - mean(ycc3d(:,:,2),'all');
cr_off = 128 - mean(ycc3d(:,:,3),'all');
ycc3d(:,:,2) = min(255, max(0, ycc3d(:,:,2) + cb_off));
ycc3d(:,:,3) = min(255, max(0, ycc3d(:,:,3) + cr_off));
img3_yc  = ycbcr2rgb(uint8(ycc3d));
gray3_yc = rgb2gray(img3_yc);
m_yc = mean(double(gray3_yc(:)));
s_yc = std(double(gray3_yc(:)));
r_yc = mean(double(img3_yc(:,:,1)),'all');
g_yc = mean(double(img3_yc(:,:,2)),'all');
b_yc = mean(double(img3_yc(:,:,3)),'all');
fprintf('\n=== P03 統計比較 ===\n');
fprintf('%-18s  Mean   Std    R      G      B     |R-B|\n', '方法');
fprintf('%-18s  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f\n', '原始',      m0_3,s0_3,r0,  g0,  b0,  abs(r0-b0));
fprintf('%-18s  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f\n', 'RGB灰世界', m_gw,s_gw,r_gw,g_gw,b_gw,abs(r_gw-b_gw));
fprintf('%-18s  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f  %5.1f\n', 'YCbCr',    m_yc,s_yc,r_yc,g_yc,b_yc,abs(r_yc-b_yc));
tiledlayout(2,3,'TileSpacing','compact','Padding','compact')
nexttile; imshow(img3);    title(sprintf('原始  R=%.0f B=%.0f |R-B|=%.0f',    r0,  b0,  abs(r0-b0)))
nexttile; imshow(img3_gw); title(sprintf('RGB灰世界  R=%.0f B=%.0f |R-B|=%.0f', r_gw,b_gw,abs(r_gw-b_gw)))
nexttile; imshow(img3_yc); title(sprintf('YCbCr  R=%.0f B=%.0f |R-B|=%.0f',    r_yc,b_yc,abs(r_yc-b_yc)))
nexttile; histogram(double(gray3(:)),   128,'BinLimits',[0,255]); xlabel('像素值'); ylabel('數量')
nexttile; histogram(double(gray3_gw(:)),128,'BinLimits',[0,255]); xlabel('像素值')
nexttile; histogram(double(gray3_yc(:)),128,'BinLimits',[0,255]); xlabel('像素值')
saveas(gcf,'output/task_b/P03_comparison.png')
imwrite(img3_gw, 'output/task_b/b3-1.png')
imwrite(img3_yc, 'output/task_b/b3-2.png')
%[text]

%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline"}
%---
