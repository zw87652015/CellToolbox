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
    public partial class ManualMove : Form
    {
        SL160 _sl160;
        private string userRx;

        public ManualMove(SL160 sl160)
        {
            InitializeComponent();
            _sl160 = sl160;
        }
       
        private void ManualMove_Load(object sender, EventArgs e)
        {
            if (_sl160.priorSDK.Cmd("controller.z.fitted.get", ref userRx, false) == Prior.PRIOR_OK)
            {
                if (userRx.Equals("0"))
                {
                    grpZ.Enabled = false;
                }
            }
        }


        private void posInt_Validating(object sender, CancelEventArgs e)
        {
            double value;
            TextBox a = (TextBox)sender;

            if (double.TryParse(a.Text, out value) != true)
            {
                e.Cancel = true;
                a.Select(0, a.Text.Length);
            }
            else
            {
                if (value < 0)
                {
                    a.Text = (-value).ToString();
                }
            }
        }

        private void btnHSMIN_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.HSM_MoveAtVelocity(-Convert.ToDouble(txtHSM.Text));
        }      
        private void btnHSMIN_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.HSM_MoveAtVelocity(0);
        }
        private void btnHSMOUT_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.HSM_MoveAtVelocity(Convert.ToDouble(txtHSM.Text));
        }
        private void btnHSMOUT_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.HSM_MoveAtVelocity(0);
        }
       

     
        private void btnHLMUP_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.HLM_MoveAtVelocity(Convert.ToDouble(txtHLM.Text)); 
        }
        private void btnHLMUP_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.HLM_MoveAtVelocity(0); 
        }
        private void btnHLMDOWN_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.HLM_MoveAtVelocity(-Convert.ToDouble(txtHLM.Text));
        }
        private void btnHLMDOWN_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.HLM_MoveAtVelocity(0); 
        }
        

        private void btnSTMRETRACT_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.STM_MoveAtVelocity(-Convert.ToDouble(txtSTM.Text));
        }
        private void btnSTMRETRACT_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.STM_MoveAtVelocity(0);
        }
        private void btnSTMEXTEND_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.STM_MoveAtVelocity(Convert.ToDouble(txtSTM.Text));
        }
        private void btnSTMEXTEND_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.STM_MoveAtVelocity(0);
        }
        


        private void btnBack_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.stage.move-at-velocity 0 -" + txtStage.Text, ref userRx, false);
        }
        
        private void btnBack_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.stage.move-at-velocity 0 0", ref userRx, false);
        }


        private void btnLeft_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.stage.move-at-velocity " + txtStage.Text + " 0", ref userRx, false);
        }
       
        private void btnLeft_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.stage.move-at-velocity 0 0", ref userRx, false);
        }


        private void btnRight_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.stage.move-at-velocity -" + txtStage.Text + " 0", ref userRx, false);
        }
       
        private void btnRight_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.stage.move-at-velocity 0 0", ref userRx, false);
        }


        private void btnForward_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.stage.move-at-velocity 0 " + txtStage.Text, ref userRx, false);
        }
       
        private void btnForward_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.stage.move-at-velocity 0 0", ref userRx, false);
        }



        private void btnZUp_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.z.move-at-velocity " + txtZ.Text, ref userRx, false);
        }
       
        private void btnZUp_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.z.move-at-velocity 0", ref userRx, false);
        }


        private void btnZDown_MouseDown(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.z.move-at-velocity -" + txtZ.Text, ref userRx, false);
        }
        
        private void btnZDown_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.priorSDK.Cmd("controller.z.move-at-velocity 0", ref userRx,false);
        }



    }
}
