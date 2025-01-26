function matlabcaller()
    % Check if Python is available
    try
        pe = pyenv;
        if isempty(pe.Version)
            pyenv('Version', '/usr/local/bin/python3'); % Adjust path as needed
        end
    catch ME
        error('Python environment not found. Please ensure Python is installed and configured in MATLAB');
    end
    
    % Add the directory containing the Python script to Python path
    if count(py.sys.path, pwd) == 0
        insert(py.sys.path, int32(0), pwd);
    end
    
    try
        % Import the Python module
        py_module = py.importlib.import_module('cell_tracking_for_usbcam');
        
        % Call the main function
        py_module.main();
        
    catch ME
        % Handle any errors
        fprintf('Error running Python script: %s\n', ME.message);
        rethrow(ME);
    end
end