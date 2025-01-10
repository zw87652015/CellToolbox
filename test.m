% Example structure of the tracking algorithm
function tracks = trackCells(cellsPerFrame, maxDistance)
    numFrames = length(cellsPerFrame);
    tracks = struct('id', {}, 'positions', {}, 'radii', {}, 'frames', {});
    currentID = 1;
    
    % Initialize tracks with first frame cells
    for i = 1:length(cellsPerFrame(1).centers)
        tracks(currentID).id = currentID;
        tracks(currentID).positions = cellsPerFrame(1).centers(i,:);
        tracks(currentID).radii = cellsPerFrame(1).radii(i);
        tracks(currentID).frames = 1;
        currentID = currentID + 1;
    end
    
    % Process subsequent frames
    for frame = 2:numFrames
        currentCenters = cellsPerFrame(frame).centers;
        previousCenters = cellsPerFrame(frame-1).centers;
        
        % Calculate distance matrix between current and previous centers
        distMatrix = pdist2(currentCenters, previousCenters);
        
        % Find closest matches within maxDistance
        [assignments, unassignedCurrent] = findNearestNeighbors(distMatrix, maxDistance);
        
        % Update existing tracks
        updateTracks(tracks, assignments, currentCenters, frame);
        
        % Create new tracks for unassigned cells
        createNewTracks(tracks, unassignedCurrent, currentCenters, frame);
    end
end