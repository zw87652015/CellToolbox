function DetectcellsButtonPushed(app, event)
    % Convert to grayscale and enhance contrast
    GrayImage = rgb2gray(app.frameForDetect);
    GrayImage = imadjust(GrayImage);

    % Check for sufficient contrast
    stdIntensity = std(double(GrayImage(:)));

    if stdIntensity < 10
        dispLogInfo(app, "No cells detected - image has insufficient contrast");
        return;
    end

    % Edge detection with less sensitive threshold
    [~,threshold] = edge(GrayImage,'sobel');
    fudgeFactor = 0.7;
    BWs = edge(GrayImage,'sobel',threshold * fudgeFactor);

    % Dilate
    se90 = strel('line',3,90);
    se0 = strel('line',3,0);
    BWsdil = imdilate(BWs,[se90 se0]);

    % Fill holes
    BWdfill = imfill(BWsdil,'holes');

    % Clear border
    BWnobord = imclearborder(BWdfill,4);

    % Erode
    seD = strel('diamond',1);
    BWfinal = imerode(BWnobord,seD);
    for i=2:10
        BWfinal = imerode(BWfinal,seD);
    end

    % Enhanced filtering with size and shape criteria
    stats = regionprops(BWfinal, 'Area', 'Perimeter', 'Circularity', 'PixelIdxList');
    
    % Create valid mask based on multiple criteria
    validMask = false(size(BWfinal));
    minCircularity = 0.3;

    for i = 1:length(stats)
        area = stats(i).Area;
        circularity = 4 * pi * area / (stats(i).Perimeter ^ 2);
        
        if area >= app.minCellSize && area <= app.maxCellSize && circularity >= minCircularity
            tempMask = false(size(BWfinal));
            tempMask(stats(i).PixelIdxList) = true;
            validMask = validMask | tempMask;
        end
    end

    BWfinal = validMask;

    % Get properties of each cell region
    stats = regionprops(BWfinal, 'Centroid', 'Area', 'PixelList');

    % Create extended circles image
    extendedImage = false(size(BWfinal));

    % Process each cell
    for i = 1:length(stats)
        pixels = stats(i).PixelList;
        centroid = stats(i).Centroid;
        distances = sqrt(sum((pixels - centroid).^2, 2));
        radius = ceil(max(distances));

        % Limit the maximum radius based on cell size constraints
        maxRadius = ceil(sqrt(app.maxCellSize / pi));  % Maximum radius based on area
        radius = min(radius, maxRadius);

        [xx, yy] = meshgrid(1:size(BWfinal,2), 1:size(BWfinal,1));
        circlemask = (xx - centroid(1)).^2 + (yy - centroid(2)).^2 <= radius^2;
        extendedImage = extendedImage | circlemask;
    end

    % Create overlay image
    overlayImage = double(app.frameForDetect);
    alpha = 0.5;
    for c=1:3
        if c == 1 % Red channel
            overlayImage(:,:,c) = overlayImage(:,:,c) .* ~extendedImage + ...
            (overlayImage(:,:,c) .* (1-alpha) + 255 * alpha) .* extendedImage;
        else  % Green and Blue channels
            overlayImage(:,:,c) = overlayImage(:,:,c) .* ~extendedImage + ...
            (overlayImage(:,:,c) .* (1-alpha)) .* extendedImage;
        end
    end
    overlayImage = uint8(overlayImage);

    % Display in app.Image
    app.Image.ImageSource = overlayImage;
    dispLogInfo(app, "Cells detected.")
end