using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading;
using System.Windows.Forms;

namespace SL160_LoaderDemo
{
    public partial class ConfigStage : Form
    {
    
         SL160 _sl160;

        enum ConfigState
        {
            Start,
            Eject,

            CheckIfTrayOnStage,

            PresentTrayForInsertion,
            LoadTrayToStage,

            CheckHotelFitted,
            InsertHotel,

            AlignStageYaxis,
            InsertTrayToMarker,
            AlignTrayWithAprtmentFloor,

            QueryInsertTrayFully,
            InsertTrayFully,

            ExtractTray,
            EjectHotels,

            End,
        };

        ConfigState state = ConfigState.Start;

        public ConfigStage(SL160 sl160)
        {
            InitializeComponent();
            _sl160 = sl160;
        }

        private void ConfigStage_Load(object sender, EventArgs e)
        {
            DoState();
        }

        private void DoState()
        {
            this.Text = "STAGE Configure: Step - " + state.ToString();

            switch (state)
            {
                case ConfigState.Start:
                {
                    grpLift.Enabled = false;
                    grpShuttle.Enabled = false;
                    lbInfo.Items.Clear();


                    lbInfo.Items.Add("This procedure calibrates the stage and Stage Transfer Mechanism (STM)");
                    lbInfo.Items.Add("to the hotels on the HLM.");
                    lbInfo.Items.Add("");

                    if (_sl160.IsFixedHeight())
                    {
                        lbInfo.Items.Add("FIXED STAGE HEIGHT SYSTEM:");
                        lbInfo.Items.Add("It should be used for a fixed height stage such as when using an OpenStand.");
                        lbInfo.Items.Add("This involves the stage XY and shuttle positions, and hotel height");
                    }
                    else
                    if (_sl160.IsCustomerVariableHeight())
                    {
                        lbInfo.Items.Add("MICROSCOPE VARIABLE STAGE HEIGHT SYSTEM:");
                        lbInfo.Items.Add("It should be used for a variable height stage controlled by users");
                        lbInfo.Items.Add("Microscope. User is responsible for establishing this height position");
                        lbInfo.Items.Add("and faithfully moving to it before loading/unloading trays.");
                    }
                    else
                    if (_sl160.IsPriorVariableHeight())
                    {
                        lbInfo.Items.Add("PRIOR VARIABLE STAGE HEIGHT SYSTEM:");
                        lbInfo.Items.Add("For a variable height stage and Prior driven Z."); 
                        lbInfo.Items.Add("This demo is responsible for establishing this Z position");
                        lbInfo.Items.Add("through the PS3 Z controls");
                    }

                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Open cabinet door and then press 'Next' to eject the Hotels");
                    btnPrev.Enabled = false;

                    // load image of ejected hotels
                    pbImage.Image = Properties.Resources._1a_hotel_loading;

                    break;
                }

                case ConfigState.Eject:
                {
                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Ejecting Hotels...please wait");
                    this.Refresh();

                    btnNext.Enabled = false;
                    _sl160.EjectHotels();
                    btnNext.Enabled = true;

                    lbInfo.Items.Add("Done...");             
                    lbInfo.Items.Add("");             
                    lbInfo.Items.Add("Press 'Next' to open stage clamp ");

                    // load picture of stage with at open clamp position and close to hotel
                    pbImage.Image = Properties.Resources._8_stage_no_tray_clamp_open;
                    break;
                }

                case ConfigState.CheckIfTrayOnStage:
                {
                    btnNext.Enabled = false;
                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Opening stage clamp...");
                    lbInfo.Refresh();

                    /* move stage to load position such that clamp is open 
                     * this enables us to move the shuttle/tray without fear of it binding
                     * to the clamp
                     * */
                    if (_sl160.StageToOpenClampPosition() != Prior.PRIOR_OK)
                    {
                        MessageBox.Show("Error moving stage to open clamp position - Please contact Prior");
                        DialogResult = System.Windows.Forms.DialogResult.Cancel;
                    }

                    lbInfo.Items.Add("Done.");
                    lbInfo.Items.Add("Moving shuttle to home position.");
                    lbInfo.Refresh();

                    /* ensure shuttle at home psoition so we can check sensor
                     * */
                    if (_sl160.StageShuttleMoveTo(0) != Prior.PRIOR_OK)
                    {
                        MessageBox.Show("Error moving to shuttle to home - Please contact Prior");
                        DialogResult = System.Windows.Forms.DialogResult.Cancel;
                    }

                    lbInfo.Items.Add("Done.");
                    lbInfo.Items.Add("Checking stage sensor state.");
                    lbInfo.Refresh();

                    

                    /* is there a tray already there ?
                     * */
                    if (_sl160.TrayOnStage())
                    {
                        // load picture of homed shuttle + tray on stage
                        pbImage.Image = Properties.Resources._10_tray_loaded_on_stage;

                        if (MessageBox.Show("A tray has been detected on the stage. Is this correct?", "Query",
                                            MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.No)
                        {
                            if (MessageBox.Show("Possible sensor fault detected - Please contact Prior\r\r" +
                                                "Do you wish to continue?", "Query",
                                                MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.No)
                            {
                                DialogResult = System.Windows.Forms.DialogResult.Cancel;
                            }
                        }

                        btnNext.Enabled = true;
                        state = ConfigState.LoadTrayToStage;
                        goto case ConfigState.LoadTrayToStage;
                    }
                    else
                    {
                        // load picture of homed shuttle and no tray on stage
                        pbImage.Image = Properties.Resources._1_stage_no_tray;
                        pbImage.Refresh();

                        if (MessageBox.Show("No tray was detected on the stage. Is this correct?", "Query",
                                            MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.No)
                        {
                            if (MessageBox.Show("Possible sensor fault detected - Please contact Prior\r\r" +
                                                  "Do you wish to continue?", "Query",
                                                  MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.No)
                            {
                                DialogResult = System.Windows.Forms.DialogResult.Cancel;
                            }
                        }

                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("OK.");
                        lbInfo.Items.Add("");
                        lbInfo.Items.Add("Press 'Next' to extend shuttle and manually load tray");
                        btnNext.Enabled = true;

                        // TODO load picture of shuttle fully extended with no tray
                      
                    }

                    break;
                }

                case ConfigState.PresentTrayForInsertion:
                {
                    //  load picture of tray fully extended with tray held in place by hand
                    pbImage.Image = Properties.Resources._9_load_tray_manually;
                    pbImage.Refresh();

                    btnPrev.Enabled = false;
                    btnNext.Enabled = false;

                    _sl160.StageShuttleMoveTo(200);

                    btnNext.Enabled = true;

                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Present tray to extended Shuttle locating it on arm");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Press 'Next' to pull tray onto stage");
                    break;
                }

                case ConfigState.LoadTrayToStage:
                {
                    // load picture of homed shuttle + tray on stage
                    pbImage.Image = Properties.Resources._10_tray_loaded_on_stage;
                    pbImage.Refresh();

                    btnPrev.Enabled = false;

                    _sl160.StageShuttleMoveTo(0);
                    
                    if (_sl160.TrayOnStage() == false)
                    {
                        if (MessageBox.Show("It seems the tray may not have loaded correctly. Is the tray fully loaded ?", "Query",
                                       MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
                        {
                            MessageBox.Show("Possible sensor fault detected - Please contact Prior");
                        }
                        
                        if (MessageBox.Show("Would you like to retry the load operation?", "Query",
                                    MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.No)
                        {
                            DialogResult = System.Windows.Forms.DialogResult.Cancel;
                        }
                        else
                        {
                            MessageBox.Show("Manually remove tray if still on stage and press Ok", "Continue");
                        }

                        /* try again
                         * */
                        state = ConfigState.PresentTrayForInsertion;
                        goto case ConfigState.PresentTrayForInsertion;
                    }
                    else
                    {
                        if (MessageBox.Show("Confirm tray loaded to stage correctly?", "Query",
                                       MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.No)
                        {
                            if (MessageBox.Show("Possible sensor fault detected - Please contact Prior!\r" +
                                            "Do you wish to continue?", "Query",
                                            MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.No)
                            {
                                DialogResult = System.Windows.Forms.DialogResult.Cancel;
                            }
                        }

                        /* pre-position shuttle ready for next alignment steps
                         * */
                        _sl160.StageShuttleMoveTo(80);

                        btnPrev.Enabled = true;
                        lbInfo.Items.Clear();

                        // :show picture of ejected shuttle and hotel loaded to  position 1
                        pbImage.Image = Properties.Resources._1a_hotel_loading;

                        lbInfo.Items.Add("Now fit hotel to position 1.");
                        lbInfo.Items.Add("Ensure no trays in apartments!");
                        lbInfo.Items.Add("");
                        lbInfo.Items.Add("Press 'Next' to continue.");
                    }
                    break;
                }
                

                case ConfigState.CheckHotelFitted:
                {
                    /* check that correct hotel is fitted 
                     * */
                    if (_sl160.HotelFitted(1) == false)
                    {
                        if (MessageBox.Show("Hotel 1 not detected!\rPlease refit and try again", "Error ",
                                     MessageBoxButtons.OKCancel, MessageBoxIcon.Exclamation) == System.Windows.Forms.DialogResult.OK)
                        {
                            /* let user try again
                             * */
                            state--;
                        }
                        else
                        {
                            DialogResult = System.Windows.Forms.DialogResult.Cancel;
                        }

                        return;
                    }

                    btnPrev.Enabled = false;


                    // :show picture of hotel1 lifted to stage aligment height
                    pbImage.Image = Properties.Resources._5_hotel_lifted_to_check_alignment;
                    pbImage.Refresh();

                    /* Load them to the now calibrated Load position
                     * */
                    _sl160.LoadHotels();

                    //if (_sl160.IsFixedHeight())
                    //{
                        /* lift hotel to known position for calibrating - this is close but tolerance build up will require 
                         * further fettling of this position
                         * */
                        _sl160.HotelLiftTo(30);
                        state = ConfigState.AlignStageYaxis;
                        goto case ConfigState.AlignStageYaxis;
                    //}
                    //else
                    //{
                    //    lbInfo.Items.Clear();
                    //    lbInfo.Items.Add("Position your variable stage height to (TBD) ");
                    //    lbInfo.Items.Add("");
                    //    lbInfo.Items.Add("Press 'Next' to continue");
                    //}

                    break;
                }


                /* if there are more pictures to display add them here as ImageHotelExtendedPlusTray,3 ... etc
                * enabling the prev button to allow backtracking to ImageHotelExtended
                * */
                case ConfigState.AlignStageYaxis:
                {
                    //  image showing tray being presented to opening of apartment, prior to insertion
                    pbImage.Image = Properties.Resources._11_align_tray_to_hotel;
                    
                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Use Y-axis of joystick to position stage to apartment opening.");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Info 1 of 3: Press 'Next' to continue.");
                    btnPrev.Enabled = false;
                    break;
                }

                case ConfigState.InsertTrayToMarker:
                {
                    //  image showing tray inserted to marker on tray side
                    pbImage.Image = Properties.Resources._13_tray_mark_aligned_to_hotel;

                    grpShuttle.Enabled = true;
                    grpLift.Enabled = true;

                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Use Stage Shuttle jog buttons to position shuttle into stage to marker.");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Info 2 of 3: Press 'Next' to continue.");
                    btnPrev.Enabled = true;
                    break;
                }

                case ConfigState.AlignTrayWithAprtmentFloor:
                {
                    // image showing tray being tapped to ensure flatness with apartment floor
                    pbImage.Image = Properties.Resources._12_adjust_hotel_loading_height;
                    
                    lbInfo.Items.Clear();
                    lbInfo.Items.Add("Use Hotel Lift jog buttons to position tray to apartment floor.");
                    lbInfo.Items.Add("Adjust height and Tap tray until there is no movement noticed.");
                    lbInfo.Items.Add("");
                    lbInfo.Items.Add("Info 3 of 3: Press 'Next' to continue");
                    btnPrev.Enabled = true;
                    break;
                }

                case ConfigState.QueryInsertTrayFully:
                {
                    //  image showing fully inserted to hotel still attached to shuttle
                    pbImage.Image = Properties.Resources._13_tray_mark_aligned_to_hotel;

                    if (MessageBox.Show("Press Ok to insert tray fully, else  Cancel and continue to adjust position", "Align ",
                                    MessageBoxButtons.OKCancel, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.OK)
                    {
                        state = ConfigState.InsertTrayFully;
                        goto case ConfigState.InsertTrayFully;
                    }

                    /* stay in this state allowing user to adjust positions as required
                     * */
                    break;
                }

                case ConfigState.InsertTrayFully:
                {
                    btnPrev.Enabled = false;

                    /* if user positioned correctly to marker then there is 20mm to go to back of the hotel 
                     */
                    _sl160.StageShuttleMoveBy(20);

                    if (MessageBox.Show("Confirm store calibration position", "Confirm",
                                                        MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
                    {
                        grpShuttle.Enabled = false;
                        grpLift.Enabled = false;

                        _sl160.StageCalibrationDone();
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("Press 'Next' to eject hotel and continue");
                    }
                    else
                    {
                        /* back shuttle off
                         */
                        _sl160.StageShuttleMoveTo(80);

                        /* go back to start of stage aligment
                         * */
                        state = ConfigState.AlignStageYaxis;
                        goto case ConfigState.AlignStageYaxis;
                    }
                    break;
                }

                case ConfigState.ExtractTray:
                {
                     /* retract shuttle slightly to unstick paddle from clamp 
                      */
                    _sl160.StageShuttleMoveBy(-2);

                    /* raise hotel up 4mm slightly so we can retract shuttle 
                     */
                    _sl160.HotelLiftBy(4);

                    /* back shuttle off by 30mm, should leave tray in apartment */
                    _sl160.StageShuttleMoveBy(-30);

                    if (MessageBox.Show("Was the tray safely loaded to the apartment?", "Confirm",
                                                  MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
                    {
                        lbInfo.Items.Clear();
                        lbInfo.Items.Add("Press 'Next' to eject hotel and finish calibration.");
                    }
                    else
                    {
                        if (MessageBox.Show("Do you wish to retry this process?", "Confirm",
                                                 MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
                        {
                            if (MessageBox.Show("Is the tray still attached to the arm?", "Confirm",
                                                     MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
                            {
                                state = ConfigState.AlignStageYaxis;
                                goto case ConfigState.AlignStageYaxis;
                            }
                            else
                            {
                                if (MessageBox.Show("Press 'Yes' to restart calibration, 'No' to abort.", "Restart?",
                                                    MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
                                {
                                    MessageBox.Show("Manually push tray fully into apartment, then Ok this box.");
                               
                                    state = ConfigState.Eject;
                                    goto case ConfigState.Eject;
                                }
                                else
                                    DialogResult = System.Windows.Forms.DialogResult.Cancel;
                            }
                        }
                        else
                        {
                            DialogResult = System.Windows.Forms.DialogResult.Cancel;
                        }
                    }

                    break;
                }
                        
                case ConfigState.EjectHotels:
                {
                    btnNext.Enabled = false;
                    btnPrev.Enabled = false;

                    _sl160.EjectHotels();
                    DialogResult = System.Windows.Forms.DialogResult.OK;
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
           if (MessageBox.Show("Are you sure you want to quit stage calibration", "Quit ",
                                   MessageBoxButtons.YesNo, MessageBoxIcon.Exclamation) == System.Windows.Forms.DialogResult.Yes)
            {
                DialogResult = System.Windows.Forms.DialogResult.Cancel;
            }
        }

        private void btnLift_Click(object sender, EventArgs e)
        {
            if (rbLift1.Checked)
                _sl160.HotelLiftBy(1);
            else
                _sl160.HotelLiftBy(0.1);
        }

        private void btnLower_Click(object sender, EventArgs e)
        {
            if (rbLift1.Checked)
                _sl160.HotelLiftBy(-1);
            else
                _sl160.HotelLiftBy(-0.1);
        }

        private void btnExtend_MouseDown(object sender, MouseEventArgs e)
        {
            if (rbShuttle5.Checked)
                _sl160.STM_MoveAtVelocity(5);
            else
                if (rbShuttle1.Checked)
                    _sl160.STM_MoveAtVelocity(1);
                else
                    _sl160.STM_MoveAtVelocity(0.1);
        }

        private void btnExtend_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.STM_MoveAtVelocity(0);
        }

        private void btnRetract_MouseDown(object sender, MouseEventArgs e)
        {
            if (rbShuttle5.Checked)
                _sl160.STM_MoveAtVelocity(-5);
            else
                if (rbShuttle1.Checked)
                    _sl160.STM_MoveAtVelocity(-1);
                else
                    _sl160.STM_MoveAtVelocity(-0.1);
        }

        private void btnRetract_MouseUp(object sender, MouseEventArgs e)
        {
            _sl160.STM_MoveAtVelocity(0);
        }

        private void btnExtend_MouseLeave(object sender, EventArgs e)
        {
            _sl160.STM_MoveAtVelocity(0);
        }

        private void btnRetract_MouseLeave(object sender, EventArgs e)
        {
            _sl160.STM_MoveAtVelocity(0);
        }
    }
}
