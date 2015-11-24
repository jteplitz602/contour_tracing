function segmented_edgelist = feature_extract(filename)

isOctave = exist('OCTAVE_VERSION', 'builtin') ~= 0;

%% Load Hand
image = imread(filename);
if(ndims(image) > 2)    
    img_gray = rgb2gray(image);
else
    img_gray = image;
end

fil_img = uint8(imfilter(double(img_gray), ones(20) / 400, 'replicate'));

%%
x = (1:size(fil_img,2));

fil = im2double(fil_img);

vein_x_img = zeros(size(fil, 1), size(fil, 2));

%%
figure
subplot(2,2,4)
imshow(fil_img);
hold on
% 
% Local minima for rows
for i = 1:size(fil,1)
    if (isOctave)
        [ymax,imax,ymin,imin] = extrema(octave_smooth(fil(i,:), 9)); % previously 10
    else
        [ymax,imax,ymin,imin] = extrema(smooth(fil(i,:), 9)); % previously 10
    end
    
    y_len = length(imin);
    y = ones(1,y_len) * i;
    plot(imin,y,'g*', 'markers',1)
    
    if (isOctave)
        vein_x_img(sub2ind(size(vein_x_img), y', imin')) = 1;
    else
        vein_x_img(sub2ind(size(vein_x_img), y', imin)) = 1;
    end
end

% Local minima for columns
% for i = 1:size(fil,2)
%     [ymax,imax,ymin,imin] = extrema(smooth(fil(:,i), 50));
%     y_len = size(imin,2);
%     y = ones(1,y_len) * i;
%     plot(y,imin,'r*', 'markers',1)
% end

% Voting to remove isolated points
copy = vein_x_img(:,:);
for i = 2:size(vein_x_img, 1)-1
    for j = 2:size(vein_x_img,2)-1
        sel = (vein_x_img(i-1:i+1,j-1:j+1));
        selSum = sum(sel(:));
        if (selSum > 1)
            copy(i,j) = 1;
        else
            copy(i,j) = 0;
        end
    end
end

% remove the junk on the left and right edges
copy(:,end-5:end) = 0;
copy(:,1:5) = 0;

subplot(2,2,1)
imshow(copy)

% remove connected components consisting of <20 pixels
isolated_removed = bwareaopen(copy, 20);
edges_filled = filledgegaps(isolated_removed, 25);

[edgelist, ~] = edgelink(edges_filled, 15); % previously 10
segmented_edgelist = lineseg(edgelist, 3); % previously 5
% drawedgelist(edgelist, ssize(isolated_removed), 1, 'rand', 2);
drawedgelist(segmented_edgelist, size(isolated_removed), 1, 'rand');

subplot(2,2,2)
imshow(edgelist2image(edgelist));

subplot(2,2,3)
drawedgelist(segmented_edgelist, size(isolated_removed), 1, 'rand');

end
