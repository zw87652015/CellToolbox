using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;

using System.Drawing;

using System.Windows.Forms;

namespace SL160_LoaderDemo
{
    public partial class Form1 : Form
    {
        private string rx = "";
        private int cubeId = 0;

        HScrollBar[] Power_ = new HScrollBar[5];
        Label[] ID_ = new Label[5];
        Label[] LVL_ = new Label[5];
        Button[] State_ = new Button[5];
        string[] ledFitted = new string[5];


        Button[] CUBE_ = new Button[7];

        public void InitOpenStandSystem()
        {

            ID_[1] = lblFluor1;
            ID_[2] = lblFluor2;
            ID_[3] = lblFluor3;
            ID_[4] = lblFluor4;

            LVL_[1] = lvl1;
            LVL_[2] = lvl2;
            LVL_[3] = lvl3;
            LVL_[4] = lvl4;

            Power_[1] = HScrollBar1;
            Power_[2] = HScrollBar2;
            Power_[3] = HScrollBar3;
            Power_[4] = HScrollBar4;

            State_[1] = btnLed1;
            State_[2] = btnLed2;
            State_[3] = btnLed3;
            State_[4] = btnLed4;

            CUBE_[1] = HH313_1;
            CUBE_[2] = HH313_2;
            CUBE_[3] = HH313_3;
            CUBE_[4] = HH313_4;
            CUBE_[5] = HH313_5;
            CUBE_[6] = HH313_6;

            rx = "";
            sl160.priorSDK.Cmd("controller.nosepiece.fitted.get", ref rx);

            if (rx.Equals("1"))
            {
                grpNosePiece.Enabled = true;
                rx = "";
                sl160.priorSDK.Cmd("controller.nosepiece.name.get", ref rx);
                grpNosePiece.Text = rx;
            }
            else
            {
                grpNosePiece.Enabled = false;
            }

            rx = "";
            sl160.priorSDK.Cmd("controller.stage.fitted.get", ref rx);

            if (rx.Equals("1"))
            {
                grpStage.Enabled = true;
                rx = "";
                sl160.priorSDK.Cmd("controller.stage.name.get", ref rx);
                grpStage.Text = rx;
            }
            else
            {
                grpStage.Enabled = false;
            } 
            
            rx = "";
            sl160.priorSDK.Cmd("controller.z.fitted.get", ref rx);

            if (rx.Equals("1"))
            {
                grpZ.Enabled = true;
                rx = "";
                sl160.priorSDK.Cmd("controller.z.name.get", ref rx);
                grpZ.Text = rx;
            }
            else
            {
                grpZ.Enabled = false;
            }

            /* find the NIKON turret */
            int fw = 0;

            for (fw = 1; fw < 7; fw++) 
            {
                rx = "";
                sl160.priorSDK.Cmd("controller.filter.fitted.get " + fw.ToString(), ref rx);

                if (rx.Equals("1") == true)
                {
                    rx = "";
                    sl160.priorSDK.Cmd("controller.filter.name.get " + fw.ToString(), ref rx);

                    if (rx.Equals("TURRET,NIKON") == true)
                    {
                        cubeId = fw;

                        /* check for cube shutter fitted */
                        rx = "";
                        sl160.priorSDK.Cmd("controller.shutter.fitted.get 1", ref rx);

                        if (rx.Equals("1"))
                        {
                            btnCubeShutter.Enabled = true;
                        }

                        break;
                    }
                }
            }

            /* check for 4th shutter fitted */
            rx = "";
            sl160.priorSDK.Cmd("controller.shutter.fitted.get 4", ref rx);

            if (rx.Equals("1"))
            {
                btnShutter4.Enabled = true;
            }

            /* find the led */
            if (cubeId != 0)
            {
                grpCube.Enabled = true;
            }

            int led = 0;

            for (led = 1; led < 5; led++)
            {
                rx = "";
                sl160.priorSDK.Cmd("controller.led.fitted.get " + led.ToString(), ref rx);

                ledFitted[led] = rx;
                if (rx.Equals("1") == true)
                {
                    grpLed.Enabled = true;

                    rx = "";
                    sl160.priorSDK.Cmd("controller.led.fluor.get " + led.ToString(), ref rx);

                    State_[led].Enabled = true;

                    ID_[led].Text = rx;

                    LVL_[led].Enabled = true;
                    Power_[led].Enabled = true;

                    rx = "";
                    if (sl160.priorSDK.Cmd("controller.led.power.get " + led.ToString(), ref rx) == Prior.PRIOR_OK)
                    {

                        string[] parms;

                        parms = rx.Split(',');
                        Power_[led].Value = Convert.ToInt32(parms[0]);
                        LVL_[led].Text = parms[0];

                        if (sl160.priorSDK.Cmd("controller.led.state.get " + led.ToString(), ref rx) == Prior.PRIOR_OK)

                        if (rx.Equals("1"))
                        {
                            State_[led].Text = "On";
                        }
                        else
                        {
                            State_[led].Text = "Off";
                        }
                    }
                }
            }
        }

        public void UpDateOpenStand()
        {
            if (sl160.connectedState == 1)
            {
                if (grpStage.Enabled == true)
                {
                    rx = "";
                    if (sl160.priorSDK.Cmd("controller.stage.position.get ", ref rx, false) == Prior.PRIOR_OK)
                    {
                        string[] xy;

                        xy = rx.Split(',');

                        lblX.Text = xy[0];
                        lblY.Text = xy[1];
                    }
                }

                if (grpZ.Enabled == true)
                {
                    rx = "";
                    if (sl160.priorSDK.Cmd("controller.z.position.get ", ref rx, false) == Prior.PRIOR_OK)
                    {
                        lblZ.Text = rx;
                    }
                }

                if (btnCubeShutter.Enabled == true)
                {
                    if (sl160.priorSDK.Cmd("controller.shutter.state.get 1", ref rx, false) == Prior.PRIOR_OK)
                    {

                        if (rx.Equals("0") == true)
                            btnCubeShutter.Text = "Shutter Closed";
                        else
                            btnCubeShutter.Text = "Shutter Open";
                    }
                }

                if (btnShutter4.Enabled == true)
                {
                    if (sl160.priorSDK.Cmd("controller.shutter.state.get 4", ref rx, false) == Prior.PRIOR_OK)
                    {
                        if (rx.Equals("0") == true)
                            btnShutter4.Text = "Kohler Illum Off";
                        else
                            btnShutter4.Text = "Kohler Illum On";
                    }
                }

                if (grpCube.Enabled == true)
                {
                    if (sl160.priorSDK.Cmd("controller.filter.position.get " + cubeId.ToString(), ref rx,false)== Prior.PRIOR_OK)
                    {
                        int cube;

                        for (cube = 1; cube < 7; cube++)
                        {
                            if (cube == Convert.ToInt32(rx))
                                CUBE_[cube].BackColor = Color.LightGreen;
                            else
                                CUBE_[cube].BackColor = SystemColors.Control;
                        }
                    }
                }

                if (grpNosePiece.Enabled == true)
                {
                    if (sl160.priorSDK.Cmd("controller.nosepiece.position.get", ref rx, false) == Prior.PRIOR_OK)
                    {
                        if (rx.Equals("1") == true)
                        {
                            MC11_1.BackColor = Color.LightGreen;
                            MC11_2.BackColor = SystemColors.Control;
                        }
                        else
                        {
                            MC11_2.BackColor = Color.LightGreen;
                            MC11_1.BackColor = SystemColors.Control;
                        }
                    }
                }
            }
        }

        private void btnCubeShutter_Click(object sender, EventArgs e)
        {
            if (btnCubeShutter.Text.Contains("Closed") == true)
                sl160.priorSDK.Cmd("controller.shutter.open 1", ref rx);
            else
                sl160.priorSDK.Cmd("controller.shutter.close 1", ref rx);
        }

        private void btnShutter4_Click(object sender, EventArgs e)
        {
            if (btnShutter4.Text.Contains("Off") == true)
                sl160.priorSDK.Cmd("controller.shutter.open 4", ref rx);
            else
                sl160.priorSDK.Cmd("controller.shutter.close 4", ref rx);
        }

    

        private void HScrollBar1_ValueChanged(object sender, EventArgs e)
        {
            HScrollBar scroll = (HScrollBar)sender;

            int led = Convert.ToInt32(scroll.Tag);

            rx = "";
            sl160.priorSDK.Cmd("controller.led.power.set " + led.ToString() + " " + scroll.Value.ToString(), ref rx);
            LVL_[led].Text = scroll.Value.ToString();
        }



        private void HH313_H_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.filter.home " + cubeId.ToString(), ref rx);
        }

        private void HH313_1_Click(object sender, EventArgs e)
        {
            Button myButton = (Button)sender;
            int filter = Convert.ToInt32(myButton.Tag);

            rx = "";
            sl160.priorSDK.Cmd("controller.filter.goto-position " + cubeId.ToString() + " " + filter.ToString(), ref rx);
        }

   

        private void MC11_H_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.nosepiece.home", ref rx);

        }

        private void MC11_1_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.nosepiece.goto-position 1", ref rx);

        }

        private void MC11_2_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.nosepiece.goto-position 2", ref rx);

        }

        private void btnB_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.stage.move-relative" + " 0 " + "-" + txtXStep.Text, ref rx);
        }

        private void btnH_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.stage.goto-position 0 0", ref rx);
        }

        private void btnL_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.stage.move-relative " + txtXStep.Text + " 0", ref rx);
        }

        private void btnR_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.stage.move-relative " + "-" + txtXStep.Text + " 0", ref rx);
        }

        private void btnF_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.stage.move-relative" + " 0 " + txtXStep.Text, ref rx);
        }



        private void btnU_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.z.move-relative " + txtZStep.Text, ref rx);
        }

        private void btnZH_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.z.goto-position 0", ref rx);
        }

        private void btnD_Click(object sender, EventArgs e)
        {
            rx = "";
            sl160.priorSDK.Cmd("controller.z.move-relative " + "-" + txtZStep.Text, ref rx);
        }


      
        private void btnLed1_Click(object sender, EventArgs e)
        {
            Button myButton = (Button)sender;
            int led = Convert.ToInt32(myButton.Tag);

            rx = "";
            sl160.priorSDK.Cmd("controller.led.state.get " + led.ToString(), ref rx);

            if (rx.Equals("1"))
            {
                sl160.priorSDK.Cmd("controller.led.state.set " + led.ToString() + " 0", ref rx);
                State_[led].Text = "Off";
            }
            else
            {
                sl160.priorSDK.Cmd("controller.led.state.set " + led.ToString() + " 1", ref rx);
                State_[led].Text = "On";
            }
        }

    }
}