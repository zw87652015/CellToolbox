using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading;
using System.Windows.Forms;

using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace SL160_LoaderDemo
{
    /* SDK is C# class wrapper for PriorScientificSDK DLL */
    public class SDK
    {
        [DllImport("PriorScientificSDK.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PriorScientificSDK_Version(StringBuilder version);

        [DllImport("PriorScientificSDK.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PriorScientificSDK_Initialise();

        [DllImport("PriorScientificSDK.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PriorScientificSDK_OpenNewSession();

        [DllImport("PriorScientificSDK.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PriorScientificSDK_CloseSession(int sessionID);
        
        [DllImport("PriorScientificSDK.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PriorScientificSDK_cmd(int session, StringBuilder tx, StringBuilder rx);

        /* this demo only supports one session */
        int _sessionID = -1;

        public SDK()
        {
             
        }


        public int GetVersion(StringBuilder version)
        {
            return PriorScientificSDK_Version(version);
        }

        public int Initialise()
        {
            return PriorScientificSDK_Initialise();
        }

        public int OpenSession()
        {
            _sessionID = PriorScientificSDK_OpenNewSession();
            return _sessionID;
        }

        public int CloseSession()
        {
            return PriorScientificSDK_CloseSession(_sessionID);
        }

        public int Cmd(string usertx, ref string userrx, bool displayError = true)
        {
            int ret;


            StringBuilder tx = new StringBuilder();
            StringBuilder rx = new StringBuilder();

            tx.Append(usertx);
            ret = PriorScientificSDK_cmd(_sessionID, tx, rx);

            if (ret == Prior.PRIOR_OK)
            {
                userrx = rx.ToString();
            }
            else
            {
                if (displayError)
                {
                    MessageBox.Show("Sent " + usertx + "\rSDK error: " + SDKerrorFromCode(ret));
                }
            }

            return ret;
        }

        /* from SDK errors.h file */
        private string SDKerrorFromCode(int ec)
        {
            switch (ec)
            {
                case 0: return "PRIOR_OK";
                case -10001: return "PRIOR_UNRECOGNISED_COMMAND";
                case -10002: return "PRIOR_FAILEDTOOPENPORT";
                case -10003: return "PRIOR_FAILEDTOFINDCONTROLLER";
                case -10004: return "PRIOR_NOTCONNECTED";
                case -10005: return "PRIOR_ALREADYCONNECTED";
                case -10007: return "PRIOR_INVALID_PARAMETERS";
                case -10008: return "PRIOR_UNRECOGNISED_DEVICE";
                case -10009: return "PRIOR_APPDATAPATHERROR";
                case -10010: return "PRIOR_LOADERERROR";
                case -10011: return "PRIOR_CONTROLLERERROR";
                case -10012: return "PRIOR_NOTIMPLEMENTEDYET";
                case -10013: return "PRIOR_COMMS_ERROR";
                case -10100: return "PRIOR_UNEXPECTED_ERROR";
                case -10200: return "PRIOR_SDK_NOT_INITIALISED";
                case -10300: return "PRIOR_SDK_INVALID_SESSION";
                case -10301: return "PRIOR_SDK_NOMORE_SESSIONS";
                default: return "unknown contact Prior (" + ec.ToString() + ")";

            }
        }
    }
}
