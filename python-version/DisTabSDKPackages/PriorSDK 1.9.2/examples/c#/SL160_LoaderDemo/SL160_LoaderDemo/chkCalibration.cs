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
    public partial class chkCalibration : Form
    {
         SL160 _sl160;

        enum ConfigState
        {
            Start,
            EjectHotels,
            CheckHotelFitted,
            LoadHotels,
            ScanHotels,
            Load1,
            UnLoad1,
            Load2,
            UnLoad2,
            Load3,
            UnLoad3,
            Load4,
            UnLoad4,
           
            End,
        };

        ConfigState state = ConfigState.Start;

        public chkCalibration(SL160 sl160)
        {
            InitializeComponent();
            _sl160 = sl160;
        }

        private void chkCalibration_Load(object sender, EventArgs e)
        {
            DoState();
        }

        private void DoState()
        {
            this.Text = "Check Calibration: Step - " + state.ToString();

            switch (state)
            {
                case ConfigState.Start:
                {
                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("This procedure runs through a step by step check of");
                    lbInfo.Items.Add("the full calibration.");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Open cabinet door and then press 'Next' to eject the Hotels.");
                    btnPrev.Enabled = false;

                    break;
                }

                case ConfigState.EjectHotels:
                {
                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Ejecting Hotels...please wait.");
                    btnNext.Enabled = false;
                    lbInfo.Refresh();
                    _sl160.EjectHotels();
                    btnNext.Enabled = true;

                    // :show picture of ejected shuttle and hotel loaded to  position 1 and 2 
                    pbImage.Image = Properties.Resources._1a_hotel_loading;

                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Fit Hotels to position 1 and 2.");
                    lbInfo.Items.Add("each with trays fitted to apartment 1 and 20 only.");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Press 'Next' to Load Hotels.");
                    break;
                }

                case ConfigState.CheckHotelFitted:
                {

                    if (_sl160.HotelFitted(1) == false)
                    {
                        MessageBox.Show("Hotel 1 not detected!", "Error ",
                                    MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
                        state = ConfigState.EjectHotels;
                        goto case ConfigState.EjectHotels;
                    } 
                    
                    if (_sl160.HotelFitted(2) == false)
                    {
                        MessageBox.Show("Hotel 2 not detected!", "Error ",
                                    MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
                        state = ConfigState.EjectHotels;
                        goto case ConfigState.EjectHotels;
                    }

                    state++;
                    goto case ConfigState.LoadHotels;
                }

                case ConfigState.LoadHotels:
                {
                    // TODO:show picture of hotel shuttle retracted and hotel in position 1 and 2

                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Loading hotels...");
                    btnNext.Enabled = false;
                    lbInfo.Refresh();

                    /* Load them to the calibrated position
                    * */
                    if (_sl160.LoadHotels() != Prior.PRIOR_OK)
                    {
                        state = ConfigState.Start;
                        goto case ConfigState.Start;
                    }

                    lbInfo.Items.Add("Done.");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Press 'Next' to scan hotels.");

                    btnNext.Enabled = true;
                    break;
                }

                case ConfigState.ScanHotels:
                {
                    // TODO:show picture of hotel beig scanned

                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Scanning hotel 1...");
                    btnNext.Enabled = false;
                    lbInfo.Refresh();

                    /* scan and check hotel 1
                    * */
                    if (_sl160.ScanHotel(1) != Prior.PRIOR_OK)
                    {
                        state = ConfigState.Start;
                        goto case ConfigState.Start;
                    }

                    if (_sl160.Apartment1and20Occupied(1) == false)
                    {
                        state = ConfigState.EjectHotels;
                        goto case ConfigState.EjectHotels;
                    }

                    lbInfo.Items.Add("Scanning hotel 2...");
                    lbInfo.Refresh();
                    /* scan and check hotel 2
                    * */
                    if (_sl160.ScanHotel(2) != Prior.PRIOR_OK)
                    {
                        state = ConfigState.Start;
                        goto case ConfigState.Start;
                    }

                    if (_sl160.Apartment1and20Occupied(2) == false)
                    {
                        state = ConfigState.EjectHotels;
                        goto case ConfigState.EjectHotels;
                    }

                    btnNext.Enabled = true;

                    lbInfo.Items.Add("Done.");
                    lbInfo.Items.Add("Press 'Next' to load Hotel 2 Apartment 1 to stage.");
                    lbInfo.Refresh();

                    break;
                }

                case ConfigState.Load1:
                {
                    if (load("2 1") != Prior.PRIOR_OK)
                    {
                        state--;
                    }
                    else
                    {
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("When load complete");
                        lbInfo.Items.Add("Press 'Next' to unload to Hotel 2 Apartment 1.");
                        lbInfo.Refresh();
                    }
                    break;
                }

                case ConfigState.UnLoad1:
                {

                    if (unload("2 1") != Prior.PRIOR_OK)
                    {
                        state--;
                    }
                    else
                    {
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("When unload complete");
                        lbInfo.Items.Add("Press 'Next' to load Hotel 2 Apartment 20.");
                        lbInfo.Refresh();
                    }
                    break;
                }

                case ConfigState.Load2:
                {
                    if (load("2 20") != Prior.PRIOR_OK)
                    {
                        state--;
                    }
                    else
                    {
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("When load complete");
                        lbInfo.Items.Add("Press 'Next' to unload to Hotel 2 Apartment 20.");
                        lbInfo.Refresh();
                    }
                    break;
                }

                case ConfigState.UnLoad2:
                {

                    if (unload("2 20") != Prior.PRIOR_OK)
                    {
                        state--;
                    }
                    else
                    {
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("When unload complete");
                        lbInfo.Items.Add("Press 'Next' to load Hotel 1 Apartment 1.");
                        lbInfo.Refresh();
                    }
                    break;
                }

                case ConfigState.Load3:
                {
                    if (load("1 1") != Prior.PRIOR_OK)
                    {
                        state--;
                    }
                    else
                    {
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("When load complete");
                        lbInfo.Items.Add("Press 'Next' to unload Hotel 1 Apartment 1.");
                        lbInfo.Refresh();
                    }
                    break;
                }

                case ConfigState.UnLoad3:
                {

                    if (unload("1 1") != Prior.PRIOR_OK)
                    {
                        state--;
                    }
                    else
                    {
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("When unload complete");
                        lbInfo.Items.Add("Press 'Next' to load Hotel 1 Apartment 20.");
                        lbInfo.Refresh();
                    }
                    break;
                }

                case ConfigState.Load4:
                {
                    if (load("1 20") != Prior.PRIOR_OK)
                    {
                        state--;
                    }
                    else
                    {
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("When load complete");
                        lbInfo.Items.Add("Press 'Next' to unload Hotel 1 Apartment 20.");
                        lbInfo.Refresh();
                    }
                    break;
                }

                case ConfigState.UnLoad4:
                {

                    if (unload("1 20") != Prior.PRIOR_OK)
                    {
                        state--;
                    }
                    else
                    {
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("When unload complete");
                        lbInfo.Items.Add("Press 'Next' to end check.");
                        lbInfo.Refresh();
                    }
                    break;
                }

                case ConfigState.End:
                {
                    DialogResult = System.Windows.Forms.DialogResult.OK;
                    break;
                }
          
            }
        }

        private int load(string id)
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            if (_sl160.StateEquals(Prior.SL160_STATE_IDLE))
            {
                err = _sl160.priorSDK.Cmd("sl160.movetostage " + id, ref userRx);
            }
            else
            {
                MessageBox.Show("Loader Not Idle", "Error ",
                            MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
            }

            return err;
        }

        private int unload(string id)
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            if (_sl160.StateEquals(Prior.SL160_STATE_IDLE))
            {
                _sl160.priorSDK.Cmd("sl160.movetohotel " + id, ref userRx);
            }
            else
            {
                MessageBox.Show("Loader Not Idle", "Error ",
                            MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
            }

            return err;
        }

        private void btnPrev_Click(object sender, EventArgs e)
        {
            if (state > 0)
            {
                state--;
                DoState();
            }
        }

        private void btnNext_Click(object sender, EventArgs e)
        {
            state++;
            DoState();
        }

        private void btnQuit_Click(object sender, EventArgs e)
        {
            string userRx = "";

            if (MessageBox.Show("Are you sure you want to quit check calibration", "Quit ",
                                  MessageBoxButtons.YesNo, MessageBoxIcon.Exclamation) == System.Windows.Forms.DialogResult.Yes)
            {
                _sl160.priorSDK.Cmd("sl160.singlestepmode.set 0", ref userRx, false);
                DialogResult = System.Windows.Forms.DialogResult.Cancel;
            }
        }

        private void chkStep_CheckedChanged(object sender, EventArgs e)
        {
            string userRx = "";

            if (chkStep.Checked == true)
            {
                _sl160.priorSDK.Cmd("sl160.singlestepmode.set 1", ref userRx,false);
                btnStep.Visible = true;
            }
            else
            {
                _sl160.priorSDK.Cmd("sl160.singlestepmode.set 0", ref userRx,false);
                btnStep.Visible = false;
            }
        }

        private void btnStep_Click(object sender, EventArgs e)
        {
            string userRx = "";

            /* send single step command */
            _sl160.priorSDK.Cmd("sl160.singlestep", ref userRx);
        }
    }
}
