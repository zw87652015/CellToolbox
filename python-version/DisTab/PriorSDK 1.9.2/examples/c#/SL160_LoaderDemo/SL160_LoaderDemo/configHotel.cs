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
    public partial class ConfigHotel : Form
    {
        SL160 _sl160;
        bool _hotelUnloaded = false;

        enum ConfigState
        {
            Start,
            EjectHotels,
            CheckHotelFitted,
            LoadHotels,
            HotelNotAlignedWithHLM,
            HotelAlignedWithHLM,
            HotelLiftedOk,
            Align,
            Confirm,
            End,
        };

        ConfigState state = ConfigState.Start;

        public ConfigHotel(SL160 sl160)
        {
            InitializeComponent();
            _sl160 = sl160;
        }

        private void ConfigHotel_Load(object sender, EventArgs e)
        {
            DoState();
        }

        private void UpdateStateText()
        {
            this.Text = "HOTEL Calibration: Step - " + state.ToString();
        }

        private void DoState()
        {
            UpdateStateText();       

            switch (state)
            {
                case ConfigState.Start:
                {
                    _hotelUnloaded = false;

                    grpAlign.Enabled = false;
                    grpLift.Enabled = false;
                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("This procedure calibrates the Hotel Shuttle Mechanism (HSM)");
                    lbInfo.Items.Add("with the Hotel Lifting Mechanism (HLM).");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Open cabinet door and then press 'Next' to eject the HSM.");
                    btnPrev.Enabled = false;
                    break;
                }

                case ConfigState.EjectHotels:
                {
                    if (_hotelUnloaded == false)
                    {
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("Ejecting Hotels...please wait.");
                        btnNext.Enabled = false;
                        lbInfo.Refresh();
                        _sl160.EjectHotels();
                        btnNext.Enabled = true;
                        _hotelUnloaded = true;
                    }

                    // :show picture of ejected hotel with hotel 1 position
                    pbImage.Image = Properties.Resources._1a_hotel_loading;

                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Fit Hotel to position 1 and then press 'Next' to continue.");
                    break;
                }

                case ConfigState.CheckHotelFitted:
                {
                    /* check that correct hotel is fitted 
                     * */
                    if (_sl160.HotelFitted(1) == false)
                    {
                        MessageBox.Show("Hotel 1 not detected!", "Error ",
                                    MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
                        state = ConfigState.EjectHotels;
                        UpdateStateText();
                        goto case ConfigState.EjectHotels;
                    }

                    state++;
                    goto case ConfigState.LoadHotels;
                }

                case ConfigState.LoadHotels:
                {
                    // :show picture of hotel shuttle retracted and hotel in position 1
                    pbImage.Image = Properties.Resources._2_and_7_hotel_at_load_position;

                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Loading hotels...");
                    btnNext.Enabled = false;
                    lbInfo.Refresh();

                    /* Load them to the default (uncalibrated) Load position
                    * */
                    _sl160.LoadHotels();
                    lbInfo.Items.Add("Done.");

                    btnNext.Enabled = true;
                    state = ConfigState.HotelNotAlignedWithHLM;
                    UpdateStateText();
                    goto case ConfigState.HotelNotAlignedWithHLM;
                }

                case ConfigState.HotelNotAlignedWithHLM:
                {
                    // :show picture of hotel 1 NOT aligned to HLM (may be more than one image needed here)
                    pbImage.Image = Properties.Resources._3_hotel_not_aligned;

                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Hotel NOT aligned with HLM.");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Info 1 of 3: Press 'Next' for more info.");
                    btnPrev.Enabled = false;

                    break;
                }

                case ConfigState.HotelAlignedWithHLM:
                {
                    // :show picture of hotel 1 aligned to HLM (may be more than one image needed here)
                    pbImage.Image = Properties.Resources._4_hotel_aligned;

                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Hotel aligned with HLM.");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Info 2 of 3: Press 'Next' for more info.");
                    btnPrev.Enabled = true;

                    break;
                }

                case ConfigState.HotelLiftedOk:
                {
                    // :show picture of hotel lifted by HLM
                    pbImage.Image = Properties.Resources._5_hotel_lifted_to_check_alignment;
         
                    grpAlign.Enabled = false;
                    grpLift.Enabled = false;

                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Hotel succesfully lifted by HLM as shown above");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Info 3 of 3: Press 'Next' to align shuttle.");
                    btnPrev.Enabled = true;

                    break;
                }

                /* if there are more pictures to display add them here as Picture2,3 ... etc
                * enabling the prev button to allow backtracking to Picture1
                * */

                case ConfigState.Align:
                {
                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Now align hotel to HLM as shown in previous images.");
                    lbInfo.Items.Add("Use controls opposite to position the shuttle and test the lift.");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Press 'Next' to confirm Hotel Shuttle calibration.");

                    grpAlign.Enabled = true;
                    grpLift.Enabled = true;
                    break;
                }

                case ConfigState.Confirm:
                {
                    if (MessageBox.Show("Are you happy with alignment", "Confirm",
                                     MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.No)
                    {
                        if (MessageBox.Show("Do you wish to retry alignment?", "Retry",
                                     MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
                        {
                            state = ConfigState.HotelNotAlignedWithHLM;
                            UpdateStateText();
                            goto case ConfigState.HotelNotAlignedWithHLM;
                        }
                        else
                            DialogResult = System.Windows.Forms.DialogResult.Cancel;
                    }
                    else
                    {
                        _sl160.HotelCalibrationDone();
                        DialogResult = System.Windows.Forms.DialogResult.OK;
                    }
                    break;
                }
            }
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
            if (MessageBox.Show("Are you sure you want to quit hotel calibration", "Quit ",
                                   MessageBoxButtons.YesNo, MessageBoxIcon.Exclamation) == System.Windows.Forms.DialogResult.Yes)
            {
                DialogResult = System.Windows.Forms.DialogResult.Cancel;
            }
        }

        private void btnHotelIn_Click(object sender, EventArgs e)
        {
            if (rb1mm.Checked == true)
                _sl160.HotelShuttleMoveBy(-1);
            else
                _sl160.HotelShuttleMoveBy(-0.1);
        }

        private void btnHotelOut_Click(object sender, EventArgs e)
        {
            if (rb1mm.Checked == true)
                _sl160.HotelShuttleMoveBy(1);
            else
                _sl160.HotelShuttleMoveBy(0.1);
        }

        private void btnLift_Click(object sender, EventArgs e)
        {
            /* dont allow shuttle alignments to occur when hotel is out of shuttle base
             * */
            grpAlign.Enabled = false;
            _sl160.HotelLiftTo(30);
        }

        private void btnLower_Click(object sender, EventArgs e)
        {
            _sl160.HotelLiftTo(0);
            grpAlign.Enabled = true;
        }

    }
}
