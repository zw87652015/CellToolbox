using System;

namespace SL160_LoaderDemo
{
    static class Prior
    {
        /* equivalent of errors.h in C-SDK */
        /* *************************************************************************************************************************** */

        /**
         * @brief SDK ERROR CODES returned directly by the SDk 
         */
        public const int PRIOR_OK = 0;
        public const int PRIOR_UNRECOGNISED_COMMAND = -10001;
        public const int PRIOR_FAILEDTOOPENPORT = -10002;
        public const int PRIOR_FAILEDTOFINDCONTROLLER = -10003;
        public const int PRIOR_NOTCONNECTED = -10004;
        public const int PRIOR_ALREADYCONNECTED = -10005;
        public const int PRIOR_INVALID_PARAMETERS = -10007;
        public const int PRIOR_UNRECOGNISED_DEVICE = -10008;
        public const int PRIOR_APPDATAPATHERROR = -10009;
        public const int PRIOR_LOADERERROR = -10010;
        public const int PRIOR_CONTROLLERERROR = -10011;
        public const int PRIOR_NOTIMPLEMENTEDYET = -10012;
        public const int PRIOR_UNEXPECTED_ERROR = -10100;
        public const int PRIOR_SDK_NOT_INITIALISED = -10200;
        public const int PRIOR_SDK_INVALID_SESSION = -10300;
        public const int PRIOR_SDK_NOMORE_SESSIONS = -10301;


        /* *************************************************************************************************************************** */

        /**
         * @brief  CONTROLLER ERROR codes returned by the stage controller being used. 
         */
        public const int PRIOR_NO_STAGE = 1;
        public const int PRIOR_NOT_IDLE = 2;
        public const int PRIOR_NO_DRIVE = 3;
        public const int PRIOR_STRING_PARSE = 4;
        public const int PRIOR_COMMAND_NOT_FOUND = 5;
        public const int PRIOR_INVALID_SHUTTER = 6;
        public const int PRIOR_NO_FOCUS = 7;
        public const int PRIOR_VALUE_OUT_OF_RANGE = 8;
        public const int PRIOR_INVALID_WHEEL = 9;
        public const int PRIOR_ARG1_OUT_OF_RANGE = 10;
        public const int PRIOR_ARG2_OUT_OF_RANGE = 11;
        public const int PRIOR_ARG3_OUT_OF_RANGE = 12;
        public const int PRIOR_ARG4_OUT_OF_RANGE = 13;
        public const int PRIOR_ARG5_OUT_OF_RANGE = 14;
        public const int PRIOR_ARG6_OUT_OF_RANGE = 15;
        public const int PRIOR_INCORRECT_STATE = 16;
        public const int PRIOR_NO_FILTER_WHEEL = 17;
        public const int PRIOR_QUEUE_FULL = 18;
        public const int PRIOR_COMP_MODE_SET = 19;
        public const int PRIOR_SHUTTER_NOT_FITTED = 20;
        public const int PRIOR_INVALID_CHECKSUM = 21;
        public const int PRIOR_NOT_ROTARY = 22;
        public const int PRIOR_NO_FOURTH_AXIS = 40;
        public const int PRIOR_AUTOFOCUS_IN_PROG = 41;
        public const int PRIOR_NO_VIDEO = 42;
        public const int PRIOR_NO_ENCODER = 43;
        public const int PRIOR_SIS_NOT_DONE = 44;
        public const int PRIOR_NO_VACUUM_DETECTOR = 45;
        public const int PRIOR_NO_SHUTTLE = 46;
        public const int PRIOR_VACUUM_QUEUED = 47;
        public const int PRIOR_SIZ_NOT_DONE = 48;
        public const int PRIOR_NOT_SLIDE_LOADER = 49;
        public const int PRIOR_ALREADY_PRELOADED = 50;
        public const int PRIOR_STAGE_NOT_MAPPED = 51;
        public const int PRIOR_TRIGGER_NOT_FITTED = 52;
        public const int PRIOR_INTERPOLATOR_NOT_FITTED = 53;
        public const int PRIOR_WRITE_FAIL = 80;
        public const int PRIOR_ERASE_FAIL = 81;
        public const int PRIOR_NO_DEVICE = 128;
        public const int PRIOR_NO_PMD_AXIS = 129;



        /**
         * @brief  SL160 loader axes defines 
         */

        public const int SL160_AXISX = 1;
        public const int SL160_AXISY = 2;
        public const int SL160_AXISZ = 3;

        public const int SL160_HSM = 1;
        public const int SL160_HLM = 2;
        public const int SL160_STM = 3;

        /**
         * @brief  SL160 loader states  
         */
        public const int SL160_STATE_STATEMASK = 0x000F00000;
        public const int SL160_STATE_SUBSTATEMASK = 0x03F000000;
        public const int SL160_STATE_UNKNOWN = 0x000000000;
        public const int SL160_STATE_SETUP = 0x000100000;
        public const int SL160_STATE_INITIALISE = 0x000200000;
        public const int SL160_STATE_STOP = 0x000300000;
        public const int SL160_STATE_IDLE = 0x000400000;
        public const int SL160_STATE_TXF_TOSTAGE = 0x000500000;
        public const int SL160_STATE_TXF_FROMSTAGE = 0x000600000;
        public const int SL160_STATE_SCANHOTEL = 0x000800000;
        public const int SL160_STATE_LOAD_HOTELS = 0x000900000;
        public const int SL160_STATE_UNLOAD_HOTELS = 0x000A00000;


        /**
         * @brief  SL160 status flags masks
         */
        public const int SL160_LOADER_ERROR = 0x0001;
        public const int SL160_LOADER_NOTCONNECTED = 0x0002;
        public const int SL160_LOADER_NOTINITIALISED = 0x0004;
        public const int SL160_LOADER_NOTSETUP = 0x0008;

        public const int SL160_LOADER_NOTIDLE = 0x0010;
        public const int SL160_LOADER_INVALIDTRAY = 0x0020;
        public const int SL160_LOADER_INVALIDHOTEL = 0x0040;
        public const int SL160_LOADER_TRAYONARM = 0x0080;
        public const int SL160_LOADER_TRAYONSTAGE = 0x0100;
        public const int SL160_LOADER_HOTELEJECTED = 0x0200;
        public const int SL160_LOADER_HOTELNOTSCANNED = 0x0800;

        public const int SL160_LOADER_COMMSERROR = 0x1000;
        public const int SL160_LOADER_TRAYSENSORERROR = 0x2000;
        public const int SL160_LOADER_AXISSTALLED = 0x8000;


        /**
         * @brief SL160 getlastError property return values
         */
        public const int SL160_ERR_OK = 0;
        public const int SL160_ERR_NOTINITIALISED = -1;
        public const int SL160_ERR_NOTSETUP = -2;
        public const int SL160_ERR_GRIPPER_HOMING_FAILED = -3;
        public const int SL160_ERR_INVALIDHOTEL = -4;
        public const int SL160_ERR_INVALIDTRAY = -5;
        public const int SL160_ERR_PLATEINGRIPPER = -7;
        public const int SL160_ERR_TRAYONSTAGE = -8;
        public const int SL160_ERR_INVALIDSTATECHANGE = -9;
        public const int SL160_ERR_HOTELREMOVED = -10;
        public const int SL160_ERR_WRONGTRAYSENSORSTATE = -11;
        public const int SL160_ERR_COMMS_ERROR = -13;
        public const int SL160_ERR_AXIS_STALLED = -14;

    };
};
