%[text] # Task A: 圖像診斷與數據分析
%[text] 計算 P01、P02、P03、T01、T02 五張影像的灰階 Mean、Std 及 RGB 各通道平均值，並繪製灰階直方圖以判斷問題類型。
%%
%[text] ## 統計計算
imgs  = {'assets/P01.jpg','assets/P02.jpg','assets/P03.jpg', ...
         'assets/T01.jpg','assets/T02.jpg'};
names = {'P01','P02','P03','T01','T02'};
n = numel(imgs);
means   = zeros(n,1);
stds    = zeros(n,1);
r_means = zeros(n,1);
g_means = zeros(n,1);
b_means = zeros(n,1);
for i = 1:n
    img  = imread(imgs{i});
    if size(img,3) == 1
        img = repmat(img,1,1,3);
    end
    gray = rgb2gray(img);
    gd   = double(gray(:));
    means(i)   = mean(gd);
    stds(i)    = std(gd);
    r_means(i) = mean(double(img(:,:,1)), 'all');
    g_means(i) = mean(double(img(:,:,2)), 'all');
    b_means(i) = mean(double(img(:,:,3)), 'all');
end
%%
%[text] ## 統計結果表格
%[text] 各圖灰階 Mean、Std 及 RGB 各通道平均值如下。
T = table(names', means, stds, r_means, g_means, b_means, ...
    'VariableNames', {'Image','Mean','Std','R_Mean','G_Mean','B_Mean'});
disp(T)
%%
%[text] ## 判斷依據
%[text] - **P01（亮度問題）**：Mean 偏低（暗）或偏高（亮），直方圖整體偏左或偏右。
%[text] - **P02（對比度問題）**：Mean ≈ 128，Std 明顯偏小，直方圖集中於中段。
%[text] - **P03（色彩問題）**：RGB 三通道平均值差異顯著（> 15），直方圖可見通道失衡。\
%%
%[text] ## 直方圖 — P01（亮度問題）
img  = imread('assets/P01.jpg');
gray = rgb2gray(img);
histogram(double(gray(:)), 256, 'BinLimits', [0,255])
title(sprintf('P01  Mean=%.1f  Std=%.1f', means(1), stds(1)))
xlabel('像素值'); ylabel('像素數量')
saveas(gcf, 'output_hist_P01.png')
%%
%[text] ## 直方圖 — P02（對比度問題）
img  = imread('assets/P02.jpg');
gray = rgb2gray(img);
histogram(double(gray(:)), 256, 'BinLimits', [0,255])
title(sprintf('P02  Mean=%.1f  Std=%.1f', means(2), stds(2)))
xlabel('像素值'); ylabel('像素數量')
saveas(gcf, 'output_hist_P02.png')
%%
%[text] ## 直方圖 — P03（色彩問題）
img  = imread('assets/P03.jpg');
gray = rgb2gray(img);
histogram(double(gray(:)), 256, 'BinLimits', [0,255])
title(sprintf('P03  Mean=%.1f  Std=%.1f', means(3), stds(3)))
xlabel('像素值'); ylabel('像素數量')
saveas(gcf, 'output_hist_P03.png')
%%
%[text] ## 直方圖 — T01
img  = imread('assets/T01.jpg');
if size(img,3) == 3; gray = rgb2gray(img); else; gray = img; end
histogram(double(gray(:)), 256, 'BinLimits', [0,255])
title(sprintf('T01  Mean=%.1f  Std=%.1f', means(4), stds(4)))
xlabel('像素值'); ylabel('像素數量')
saveas(gcf, 'output_hist_T01.png')
%%
%[text] ## 直方圖 — T02
img  = imread('assets/T02.jpg');
if size(img,3) == 3; gray = rgb2gray(img); else; gray = img; end
histogram(double(gray(:)), 256, 'BinLimits', [0,255])
title(sprintf('T02  Mean=%.1f  Std=%.1f', means(5), stds(5)))
xlabel('像素值'); ylabel('像素數量')
saveas(gcf, 'output_hist_T02.png')
%[text]

%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline"}
%---
