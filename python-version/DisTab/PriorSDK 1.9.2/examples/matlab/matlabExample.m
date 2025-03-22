%load the PriorScientificSDK library
if not(libisloaded('PriorScientificSDK'))   
    loadlibrary('PriorScientificSDK','PriorScientificSDK.h','alias','Prior')
end

libfunctions('Prior')

rx = blanks(1024)

%check API version
[apistatus,rx] = calllib('Prior','PriorScientificSDK_Version',rx)

%initialise PriorSDK
[apistatus] = calllib('Prior','PriorScientificSDK_Initialise')

%create a session to control a stage controller and/or other devices
[session] = calllib('Prior','PriorScientificSDK_OpenNewSession')

%my controller was on COM3
cmd = 'controller.connect 3'
[apistatus,cmd,rx] = calllib('Prior','PriorScientificSDK_cmd',session, cmd, rx)

%get the stage position
cmd = 'controller.stage.position.get'
[apistatus,cmd,rx] = calllib('Prior','PriorScientificSDK_cmd',session, cmd, rx)

%when finished disocnnect the COM connection to the controller
cmd = 'controller.disconnect'
[apistatus,cmd,rx] = calllib('Prior','PriorScientificSDK_cmd',session, cmd, rx)

%close the session
[apistatus] = calllib('Prior','PriorScientificSDK_CloseSession',session)

%unload the library from MatLab
unloadlibrary Prior