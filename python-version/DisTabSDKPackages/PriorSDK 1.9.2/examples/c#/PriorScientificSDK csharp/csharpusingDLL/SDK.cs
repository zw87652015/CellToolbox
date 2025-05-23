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

namespace csharpusingDLL
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
            return PriorScientificSDK_OpenNewSession();
        }

        public int CloseSession(int sessionID)
        {
            return PriorScientificSDK_CloseSession(sessionID);
        }

        public int Cmd(int session, string usertx, ref string userrx, bool displayError = true)
        {
            int ret;

            StringBuilder tx = new StringBuilder();
            StringBuilder rx = new StringBuilder();

            tx.Append(usertx);
            ret = PriorScientificSDK_cmd(session,tx,rx);

            if (ret == Prior.PRIOR_OK)
            {
                userrx = rx.ToString();
            }
            else
            {
                if (displayError)
                {
                    MessageBox.Show("Sent " + usertx + "\rSDK error: " + ret.ToString() );
                }
            }

            return ret;
        }
    }
}
