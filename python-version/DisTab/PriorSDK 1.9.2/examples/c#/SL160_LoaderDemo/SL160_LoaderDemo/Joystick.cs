using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace SL160_LoaderDemo
{
    public partial class Joystick : Form
    {
        private string xdir = "";
        private string ydir = "";
        SL160 _sl160;
        string rxBuf = "";

        public Joystick(SL160 sl160)
        {
            InitializeComponent();
            _sl160 = sl160;
        }

        private void Joystick_Load(object sender, EventArgs e)
        {
            string[] parms;

            _sl160.priorSDK.Cmd("controller.stage.joystickdirection.get", ref rxBuf);

            parms = rxBuf.Split(' ');
            xdir = parms[0];
            ydir = parms[1];

            chkX.CheckedChanged -= chkX_CheckedChanged;
            chkY.CheckedChanged -= chkY_CheckedChanged;

            if (xdir.Equals("-1"))
                chkX.Checked = true;
            else
                chkX.Checked = false; 
            
            if (ydir.Equals("-1"))
                chkY.Checked = true;
            else
                chkY.Checked = false;

            chkX.CheckedChanged += chkX_CheckedChanged;
            chkY.CheckedChanged += chkY_CheckedChanged;

            /* check joystick enabled state 
             * */

            _sl160.priorSDK.Cmd("controller.stage.joyxyz.state.get", ref rxBuf);

            /* prevtn event from firing as we update the gui
             * */
            rbXYZ.CheckedChanged -= rbXYZ_CheckedChanged;
            rbOff.CheckedChanged -= rbOff_CheckedChanged;
            rbXY.CheckedChanged -= rbXY_CheckedChanged;
            rbZ.CheckedChanged -= rbZ_CheckedChanged;

            if (rxBuf.Equals("0"))
                rbXYZ.Checked = true;
            else if (rxBuf.Equals("1"))
                rbOff.Checked = true;
            else if (rxBuf.Equals("2"))
                rbXY.Checked = true;
            else if (rxBuf.Equals("3"))
                rbZ.Checked = true;

            rbXYZ.CheckedChanged += rbXYZ_CheckedChanged;
            rbOff.CheckedChanged += rbOff_CheckedChanged;
            rbXY.CheckedChanged += rbXY_CheckedChanged;
            rbZ.CheckedChanged += rbZ_CheckedChanged;
        }

        private void chkX_CheckedChanged(object sender, EventArgs e)
        {
            if (chkX.Checked == false)
                xdir = "1";
            else
                xdir = "-1";

            _sl160.priorSDK.Cmd("controller.stage.joystickdirection.set " +
                                xdir + " " + ydir, ref rxBuf);
        }

        private void chkY_CheckedChanged(object sender, EventArgs e)
        {
            if (chkY.Checked == false)
                ydir = "1";
            else
                ydir = "-1";

            _sl160.priorSDK.Cmd("controller.stage.joystickdirection.set " +
                                xdir + " " + ydir, ref rxBuf);
        }

        private void rbXYZ_CheckedChanged(object sender, EventArgs e)
        {
            if (rbXYZ.Checked == true)
                _sl160.priorSDK.Cmd("controller.stage.joyxyz.state.set 0", ref rxBuf);
        }

        private void rbOff_CheckedChanged(object sender, EventArgs e)
        {
            if (rbXYZ.Checked == true)
                _sl160.priorSDK.Cmd("controller.stage.joyxyz.state.set 1", ref rxBuf);
        }

        private void rbZ_CheckedChanged(object sender, EventArgs e)
        {
            if (rbXYZ.Checked == true)
                _sl160.priorSDK.Cmd("controller.stage.joyxyz.state.set 2", ref rxBuf);
        }

        private void rbXY_CheckedChanged(object sender, EventArgs e)
        {
            if (rbXYZ.Checked == true)
                _sl160.priorSDK.Cmd("controller.stage.joyxyz.state.set 3", ref rxBuf);
        }

    }
}
