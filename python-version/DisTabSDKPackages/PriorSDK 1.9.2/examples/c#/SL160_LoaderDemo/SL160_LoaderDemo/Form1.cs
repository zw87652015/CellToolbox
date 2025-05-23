
/**
 * @file    SL160_LoaderDemo
 * @author	Rob Wicker  (rwicker@prior.com)
 * @date    5/5/2020
 * @brief   This project contains an SL160_LoaderDemo utility
 * @copyright   Copyright (c) 2020- Prior Scientific Instruments Ltd. All rights reserved
 *
 * This software is provided 'as is' without warranty of any kind, either express or implied,
 * including, but not limited to, the implied warranties of fitness for a purpose, or the
 * warranty of non-infringement. Without limiting the foregoing, Prior Scientific
 * makes no warranty that:
 * 
 *    1. the software will meet your requirements
 *    2. the software will be uninterrupted, timely, secure or error-free
 *    3. the results that may be obtained from the use of the software will be effective,
 *       accurate or reliable
 *    4. the quality of the software will meet your expectations
 *    5. any errors in the software obtained will be corrected.
 * 
 * Software and its documentation made available from Prior:
 * 
 *    6. could include technical or other mistakes, inaccuracies or typographical errors.
 *       Prior may make changes to the software or documentation made available.
 *    7. may be out of date, and Prior makes no commitment to update such materials.
 * 
 * Prior assumes no responsibility for errors or ommissions in the software or documentation
 * available from its web site. In no event shall Prior be liable to you or any third
 * parties for any special, punitive, incidental, indirect or consequential damages of any
 * kind, or any damages whatsoever, including, without limitation, those resulting from loss
 * of use, data or profits, whether or not Prior has been advised of the possibility of such
 * damages, and on any theory of liability, arising out of or in connection with the use of
 * this software.
 * The use of this software is at your own discretion
 * and risk and with agreement that you will be solely responsible for any damage to your
 * computer system or loss of data that results from such activities. No advice or information,
 * whether oral or written, obtained by you from Prior shall create
 * any warranty for the software.
 * 
 * HISTORY
 * 2.3      29/9/22     Updated some images and corrected spellings.
 * 2.2      25/10/21    Adding manual move capability for Pinc
 *                      Encourage user to re-initialise after an emergency stop
 *                      -TS command line argument to work with Trade Show openstand controls
 * 2.1      3/8/21      Total rework of the calibration system for people who cant follow instructions. 
 *                      Also includes provision for systems with non fixed height stages.
 *                      options to disable preview mode 
 *                      otions to control joystick direction and enabled state
 *                      tooltips added
 * 
 * 1.8      5/7/21      reverse joystick X default direction
 * 1.7      14/5/21     fixed bug in SDK class. tx/rx stringbuilders should not be static. Causes threading issues. 
 * 1.6      5/3/21      position the stage close to the load/unload target such that the clamp automatically
 *                      opens when user is prompted to insert tray during production calibration
 * 1.5      5/1/21      Added a simple stage raster example during soak
 *                      reworked calibration to use Load/unload hotels dll api calls.
 * 1.4      4/1/21      move STM out a further 10mm when user inserts tray during calibration
 *                      HSM jog buttons enabled by default
 * 1.3      19/11/20    STM axes is now encoded
 * 1.2      5/11/20     HLM and HSM are now encoded axes (STM to follow)
 * 1.1      1/4/20      initial version
 */

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using System.Diagnostics;

using System.IO;
using SL160_LoaderDemo.Properties;

namespace SL160_LoaderDemo
{
    public partial class Form1 : Form
    {
        StringBuilder dllVersion = new StringBuilder();

        bool openStandFitted = false;
        int err;

        string userTx = "";
        string userRx = "";

        /* background thread that handles the status updates from the loader */
        private BackgroundWorker RobotStatusHandling = new BackgroundWorker();

        /* create a helper class for our Sl160 application 
         * */
        public SL160 sl160 = new SL160();

        Stopwatch myStopWatch = new Stopwatch();

        /* SL160 has two hotel with 20 apartments, each apartment has an associated tray with 4 slides */
        Button[] hotel1;
        Button[] hotel2;

        public Form1()
        {
            InitializeComponent();
        }


        private void Form1_Load(object sender, EventArgs e)
        {
            /* check parameters for -TS tradeshow option */
            String[] arguments = Environment.GetCommandLineArgs();

            if (arguments.Length == 2)
            {
                if (arguments[1].Equals("-TS"))
                {
                    /* we expect certain devices to be fitted on the openstand */
                    openStandFitted = true;
                }
            }

            /* check for DLL 
             */
            try
            {
                if ((err = sl160.priorSDK.GetVersion(dllVersion)) != Prior.PRIOR_OK)
                {
                    MessageBox.Show("Error getting Prior SDK version (" + err.ToString() + ")");
                    this.Close();
                    return;
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error accessing PriorScientificSDK.dll (" + ex.Message + ")");
                this.Close();
                return;
            }

            /* initiliase DLL, *must* be done before opening a session 
             */
            if ((err = sl160.priorSDK.Initialise()) != Prior.PRIOR_OK)
            {
                MessageBox.Show("Error (" + err.ToString() + ") Initialising SDK " + dllVersion);
                this.Close();
                return;
            }

            lblstate.Text = "         ";
            lbltime.Text = "    ";
            lbllasterror.Text = "          ";

            /* use buttons as apartment visuals 
             */
            hotel1 = new Button[sl160.maxApartments];
            hotel2 = new Button[sl160.maxApartments];


            /* create the hotel apartments 
            */
            createApartments(grpHotel1, hotel1);
            createApartments(grpHotel2, hotel2);

            grpHotel1.Enabled = false;
            grpHotel2.Enabled = false;

            /* create a session in the DLL, this gives us one controller and an Sl160 loader. Multiple connections allow control of multiple
            * stage/loaders but is outside the brief for this demo
            */
            if ((err = sl160.priorSDK.OpenSession()) != Prior.PRIOR_OK)
            {
                MessageBox.Show("Error (" + err + ") Creating session in SDK " + dllVersion);
                this.Close();
                return;
            }

            if (openStandFitted)
            {
                this.Width = grpLed.Left + grpLed.Width + 20;
            }

            RobotStatusHandling.WorkerReportsProgress = true;
            RobotStatusHandling.WorkerSupportsCancellation = true;
            RobotStatusHandling.ProgressChanged += new ProgressChangedEventHandler(RobotStatusHandling_ProgressChanged);
            RobotStatusHandling.DoWork += new DoWorkEventHandler(RobotStatusHandling_DoWork);

            RobotStatusHandling.RunWorkerAsync();
        }

        private void createApartments(GroupBox grp, Button[] hotel)
        {
            int apartment;

            for (apartment = 0; apartment < sl160.maxApartments; apartment++)
            {
                // Create a Button object 
                Button apt = new Button();

                // Set Button properties
                apt.Height = 18;
                apt.Width = grp.Width - 18;
                apt.BackColor = SystemColors.Control;
                apt.ForeColor = SystemColors.ControlText;
                apt.Location = new Point(9, 15 + (sl160.maxApartments - 1 - apartment) * 20);
                apt.Tag = grp.Tag + " " + (apartment + 1).ToString();
                apt.TabStop = false;

                apt.Click += new EventHandler(button1_Click);
                grp.Controls.Add(apt);
                hotel[apartment] = apt;
            }
        }

        private int Connect()
        {
            string value = "";
            int port = 0;
            long open = Prior.PRIOR_OK;

            connectToolStripMenuItem.Text = "Connecting...";
            this.Refresh();

            /* try to connect to the stage controller 
             */
            value = Settings.Default.PS3PORT;
            open = Prior.PRIOR_OK;

            do
            {
                port = Convert.ToInt32(value);

                /* SL160 inside the PS3, so connect to PS3 first 
                 */
                open = sl160.priorSDK.Cmd("controller.connect " + port.ToString(), ref userRx);

                if (open != Prior.PRIOR_OK)
                {
                    value = "0";

                    if (InputBox.Show("SL160 Connection",
                                    "Enter Com Port:", ref value) != DialogResult.OK)
                    {
                        connectToolStripMenuItem.Text = "Connect";
                        return -1;
                    }
                }
            }
            while (open != Prior.PRIOR_OK);

            Settings.Default.PS3PORT = value;

            /* then try to connect to the sl160 - it actually doesnt matter what you use here as the port number but for 
             * clarity use the PS3 port opened above 
             */
            userTx = "sl160.connect " + port.ToString();
            open = sl160.priorSDK.Cmd(userTx, ref userRx, false);

            if (open != Prior.PRIOR_OK)
            {
                MessageBox.Show("Error (" + open.ToString() + ") connecting to SL160 Loader", "Error ",
                                MessageBoxButtons.OK, MessageBoxIcon.Error);

                connectToolStripMenuItem.Text = "Connect";
                return -1;
            }


            /* IMPORTANT:
             * Prior SL160 demo uses the following system settings:
             * STAGE:
             * stage back right as XY zero reference point. Reported positions are incrementing
             * as stage moves forward and left. stage resolution is in microns.
             * Z:
             * If stage not a fixed height Z (ie stage focusing) then this application must control Z (if its a Prior device)
             * In those circumstances Z zero position is lowest stage position. Positions in 100nm steps, increasing as stage moves up.
             * If stage height controlled by a users microscope then the users final application must initailise and guarentee repeatability 
             * of positioning Z to the calibrated point.
             * 
             * stored calibration data in the stage eeprom is dependent on these settings. Changing stage orientation/resolution 
             * from user program will invalidate stored calibration and this programs functionality.
             * It is possible for user to change but requires modifications in the demo app and re-calibration
             */

            /* 
             * default PS3 stage movment +y+y = stage front and right
            * set orientation of stage -x+y = stage left and stage forward 
            */
            sl160.priorSDK.Cmd("controller.stage.hostdirection.set -1 1", ref userRx, false);

            sl160.priorSDK.Cmd("controller.stage.joystickdirection.set -1 1", ref userRx, false);

            /* grab some initial status from the loader 
             */
            sl160.PollStatus();

            /* save the selected control port 
             */
            Settings.Default.Save();

            /* get flags from controller. Actually they are stored in the stage eeprom
             * */
            sl160.LoadCalibrationFlagsFromController();

            this.Visible = false;

            /* check device type 
             */
            if (sl160.NoDeviceTypeSet())
            {
                using (selectType type = new selectType(sl160))
                {
                    if (type.ShowDialog() != System.Windows.Forms.DialogResult.OK)
                    {
                        this.Visible = true;
                        Disconnect();
                        return -1;
                    }
                }
            }

            /* perform required initialisation of loader and stage
             * loader is initialised by DLL API call, stage/z is initialised by users application (this demo)
             * */
            using (initialise init = new initialise(sl160))
            {
                if (init.ShowDialog() != System.Windows.Forms.DialogResult.OK)
                {
                    this.Visible = true;
                    Disconnect();
                    return -1;
                }
            }

            /* update sl160 status 
             */
            sl160.PollStatus();

            if (sl160.StatusBitIsSet(Prior.SL160_LOADER_NOTSETUP))
            {
                /* some part of the calibration is incomplete 
                 */

                bool hotelCalibrated = false;
                bool stageCalibrated = false;

                if (sl160.RequiresHotelCalibration())
                {
                    /* hotel position needs calibrating, this sets the HSM aligment to 
                     * the HLM 
                     * */
                    using (ConfigHotel hotel = new ConfigHotel(sl160))
                    {
                        if (hotel.ShowDialog() == System.Windows.Forms.DialogResult.OK)                     
                            hotelCalibrated = true;
                    }
                } 
                
                if (sl160.RequiresStageCalibration())
                {
                    /* stage load position needs calibrating, this sets the XY(Z) of the
                     * stage to the HLM 
                     * */
                    using (ConfigStage stage = new ConfigStage(sl160))
                    {
                        if (stage.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                            stageCalibrated = true;
                    }
                }

                /* calibration only currently being held in controller ram, we must commit this
                 * to the stage eeprom for permanant backup
                 * */
                if (hotelCalibrated || stageCalibrated)
                {
                    string msg;

                    if (hotelCalibrated && stageCalibrated)
                        msg = "Do you wish to commit hotel and stage calibration to the SL160?\r";
                    else if (hotelCalibrated)
                        msg = "Do you wish to commit hotel calibration to the SL160?\r";
                    else
                        msg = "Do you wish to commit stage calibration to the SL160?\r";

                    if (MessageBox.Show( msg, "Confirm",
                                    MessageBoxButtons.YesNo,MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
                    {
                        Thread oThread = new Thread(SaveCalibrationToControllerNVRAM);
                        oThread.Start();
                        MessageBox.Show("Saving to controller...this will take several seconds.\r" +
                                        "After closing this window the SL160\r" +
                                        "will automatically disconnect when operation complete.\r" +
                                        "Reconnect to SL160 if you wish to continue", "info");

                        oThread.Join();
                    }
                }

                /* must disconnect and reconnect to ensure calibration updated correctly
                 * */
                this.Visible = true;
                Disconnect();
                return Prior.PRIOR_OK;
            }


            if (openStandFitted)
                InitOpenStandSystem();

            this.Visible = true;

            /* check if there is tray left on the stage
             * */
            sl160.PollStatus();

            grpAction.Enabled = true;
            btnStop.Enabled = true;

            /* in exceptional cirsumstances we may end up with a tray still on the stage, be nice and inform the 
             * user of this and how to handle it
             * */
            if (sl160.TrayOnStage())
            {
                MessageBox.Show("Sensor reports a tray is on the stage.\r" + 
                                "It can be unloaded to an empty apartment after hotels loaded and scanned.\r" +
                                "If there is no tray then there may be a sensor fault. Contact Prior Support Team");
            }

            /* extract the XYZ stage calibrated position, we dont use this 
             */
            sl160.LoadStageXYZCalibration();

            previewOnToolStripMenuItem.Checked = true;

            /* disable joystick */
            sl160.priorSDK.Cmd("controller.stage.joyxyz.off", ref userRx, false);

            return Prior.PRIOR_OK;
        }

        private void SaveCalibrationToControllerNVRAM()
        {
            /* stop the background status thread fronm running */
            pollStatus = false;
            Thread.Sleep(200);

            /* save the data to tbe stage eeprom */
            sl160.SaveCalibrationToController();

            /* start the status polling */
            pollStatus = true;
        }

        private void Disconnect()
        {
            try
            {
                int err;

                /* re-enable any joystick fitted 
                 */
                err = sl160.priorSDK.Cmd("controller.stage.joyxyz.on", ref userRx, false);

                /* disconnect from stage controller and loader 
                 */
                err = sl160.priorSDK.Cmd("sl160.disconnect", ref userRx, false);
                err = sl160.priorSDK.Cmd("controller.disconnect", ref userRx, false);

            }
            catch (Exception a)
            {
                MessageBox.Show("Disconnect(): " + a.Message);
            }

            connectToolStripMenuItem.Text = "Connect";
            this.Refresh();

            grpCube.Enabled = false;
            grpLed.Enabled = false;
            grpStage.Enabled = false;
            grpZ.Enabled = false;
            grpNosePiece.Enabled = false;
            btnShutter4.Enabled = false;
        }

        private void connectToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (sl160.connectedState == 0)
            {
                Connect();
            }
            else
            {
                Disconnect();
                connectToolStripMenuItem.Text = "Connect";
            }
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (sl160.sessionID >= 0)
            {
                Disconnect();

                /* close session */
                err = sl160.priorSDK.CloseSession();
            }
        }

        enum transferType
        {
            transferNone,
            transferToStage,
            transferToHotel
        };

        transferType userRequest = transferType.transferNone;

        private void btnToStage_Click(object sender, EventArgs e)
        {
            if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
            {
                userRequest = transferType.transferToStage;
            }
        }

        private void btnToHotel_Click(object sender, EventArgs e)
        {
            if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
            {
                userRequest = transferType.transferToHotel;
            }
        }



        private void button1_Click(object sender, EventArgs e)
        {
            /* all tray click events come though here. The controls tag selects the hotel/apartment number 
             */

            string tag = ((Button)sender).Tag.ToString();

            if (userRequest == transferType.transferToHotel)
            {
                if (sl160.StageBusy() == 0)
                    sl160.priorSDK.Cmd("sl160.movetohotel " + tag, ref userRx);
                else
                    MessageBox.Show("Stage is currently busy!", "Error ",
                                      MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            else
                if (userRequest == transferType.transferToStage)
                {
                    if (sl160.StageBusy() == 0)
                        sl160.priorSDK.Cmd("sl160.movetostage " + tag, ref userRx);
                    else
                        MessageBox.Show("Stage is currently busy!", "Error ",
                                          MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
                else
                {
                    // ignore
                }

            userRequest = transferType.transferNone;
        }


        private void singleStepModeToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (singleStepModeToolStripMenuItem.Checked == true)
            {
                sl160.priorSDK.Cmd("sl160.singlestepmode.set 1", ref userRx);
            }
            else
            {
                sl160.priorSDK.Cmd("sl160.singlestepmode.set 0", ref userRx);
            }

            btnSingle.Enabled = singleStepModeToolStripMenuItem.Checked;
        }


        private void helpToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Form h = new help(dllVersion);

            h.Show();

        }

      
     


        private void doSoakToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (doSoakToolStripMenuItem.Checked == true)
            {
                if (sl160.StateNotEquals(Prior.SL160_STATE_IDLE) || (mySoakState != SoakState.soakIdle))
                {
                    MessageBox.Show("System must be Idle to Start Full Soak", "Error ",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);

                    doSoakToolStripMenuItem.Checked = false;
                }
                else
                {
                    int platesFitted = 0;
                    int plate;
                    int hotel;

                    for (hotel = 1; hotel <= sl160.maxHotels; hotel++)
                    {
                        for (plate = 1; plate <= sl160.maxApartments; plate++)
                        {
                            if ((err = sl160.priorSDK.Cmd("sl160.trayfitted.get " + hotel.ToString() + " " + plate.ToString(), ref userRx, false))
                                                                == Prior.PRIOR_OK)
                            {
                                platesFitted += Convert.ToInt32(userRx);
                            }
                        }
                    }

                    if (platesFitted > 0)
                    {
                        /* turn joystick off and wait in case joystick was active and stage moving
                         */
                        sl160.priorSDK.Cmd("controller.stage.joyxyz.off", ref userRx, false);
                        sl160.WaitUntilStageIdle();

                        StartSoak();
                    }
                    else
                    {
                        MessageBox.Show("There must be at least one tray in hotels", "Error ",
                                        MessageBoxButtons.OK, MessageBoxIcon.Information);

                        doSoakToolStripMenuItem.Checked = false;
                    }

                }
            }
            else
            {
                if (mySoakState < SoakState.soakScan1)
                    StopSoak();
            }
        }

        private void scanOnlySoakToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (scanOnlySoakToolStripMenuItem.Checked == true)
            {
                if (sl160.StateNotEquals(Prior.SL160_STATE_IDLE) || (mySoakState != SoakState.soakIdle))
                {
                    MessageBox.Show("System must be Idle to Start Full Soak", "Error ",
                                            MessageBoxButtons.OK, MessageBoxIcon.Information);

                    scanOnlySoakToolStripMenuItem.Checked = false;
                }
                else
                {
                    int fitted = 0;

                    if ((err = sl160.priorSDK.Cmd("sl160.hotelfitted.get 1", ref userRx, false)) == Prior.PRIOR_OK)
                    {
                        fitted += Convert.ToInt32(userRx);
                    }

                    if ((err = sl160.priorSDK.Cmd("sl160.hotelfitted.get 2", ref userRx, false)) == Prior.PRIOR_OK)
                    {
                        fitted += Convert.ToInt32(userRx);
                    }

                    if (fitted != 0)
                    {
                        StartScanSoak();
                    }
                    else
                    {
                        MessageBox.Show("There must be at least one hotel fitted", "Error ",
                                        MessageBoxButtons.OK, MessageBoxIcon.Information);

                        scanOnlySoakToolStripMenuItem.Checked = false;
                    }
                }
            }
            else
            {
                if (mySoakState >= SoakState.soakScan1)
                    StopSoak();
            }
        }

        private void btnSingle_Click(object sender, EventArgs e)
        {
            /* send single step command */
            sl160.priorSDK.Cmd("sl160.singlestep", ref userRx);
        }


        private void loaderINIToolStripMenuItem_Click(object sender, EventArgs e)
        {
            string parameters;

            string serialNumber = "";

            if (sl160.priorSDK.Cmd("controller.serialnumber.get", ref serialNumber) == Prior.PRIOR_OK)
            {
                parameters = Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData) + "/Prior/SL160_LOADER_DATA-" + serialNumber + ".ini";
                System.Diagnostics.Process.Start("Notepad.exe", parameters);
            }
        }

        private void btnEjectHotels_Click(object sender, EventArgs e)
        {
            if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
            {
                userRequest = transferType.transferNone;

                /* unload hotels */
                sl160.priorSDK.Cmd("sl160.unloadhotels", ref userRx);
            }
        }

        private void btnLoadHotels_Click(object sender, EventArgs e)
        {
            if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
            {
                userRequest = transferType.transferNone;

                /* load hotels*/
                sl160.priorSDK.Cmd("sl160.loadhotels", ref userRx);
            }
        }


        private void btnPreview_Click(object sender, EventArgs e)
        {
            sl160.priorSDK.Cmd("sl160.previewstate.set 0", ref userRx);
        }

        private void btnScan1_Click(object sender, EventArgs e)
        {
            if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
            {
                userRequest = transferType.transferNone;

                if (sl160.StageBusy() == 0)
                {
                    /* scan hotel 1*/
                    sl160.priorSDK.Cmd("sl160.scanhotel 1", ref userRx);
                }
                else
                    MessageBox.Show("Stage is currently busy!", "Error ",
                                      MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void btnScan2_Click(object sender, EventArgs e)
        {
            if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
            {
                userRequest = transferType.transferNone;

                if (sl160.StageBusy() == 0)
                {
                    /* scan hotel 2*/
                    sl160.priorSDK.Cmd("sl160.scanhotel 2", ref userRx);
                }
                else
                    MessageBox.Show("Stage is currently busy!", "Error ",
                                      MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }



        private void enabledToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (enabledToolStripMenuItem.Checked == true)
            {
                err = sl160.priorSDK.Cmd("dll.log.on", ref userRx);
                enabledToolStripMenuItem.Text = "On";
            }
            else
            {
                err = sl160.priorSDK.Cmd("dll.log.off", ref userRx);
                enabledToolStripMenuItem.Text = "Off";
            }
        }

        private void redoCalibrationToolStripMenuItem_Click(object sender, EventArgs e)
        {
            using (redoCalibration calib = new redoCalibration(sl160))
            {
                if (calib.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                {
                    Thread oThread = new Thread(SaveCalibrationToControllerNVRAM);
                    oThread.Start();
                    MessageBox.Show("Saving Flags to controller...this will take several seconds\r" +
                                    "The SL160 will automatically disconnect when complete.\r" +
                                    "Reconnect to SL160 if you wish to continue", "info");

                    oThread.Join();

                    /* now delete the INi file also
                     * */
                    string iniFileName;

                    string serialNumber = "";

                    if (sl160.priorSDK.Cmd("controller.serialnumber.get", ref serialNumber) == Prior.PRIOR_OK)
                    {
                        iniFileName = Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData) + "/Prior/SL160_LOADER_DATA-" + serialNumber + ".ini";
       
                        try
                        {
                            File.Delete(iniFileName);
                        }
                        catch (IOException ioExp)
                        {
                            MessageBox.Show(ioExp.Message);
                        }   
                    }
                   
                    Disconnect();
                }
            }
        }

        private void checkCalibrationToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (sl160.StatusBitIsSet(Prior.SL160_LOADER_NOTSETUP) == false)
            {
                previewOnToolStripMenuItem.Checked = false;

                using (chkCalibration chk = new chkCalibration(sl160))
                {
                    if (chk.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                    {

                    }
                }

                previewOnToolStripMenuItem.Checked = true;
            }
        }

        //private void moveStageOffLoaddebugToolStripMenuItem_Click(object sender, EventArgs e)
        //{
        //    sl160.priorSDK.Cmd("controller.stage.goto-position 50000 35000", ref userRx);
        //}

        private void joystickToolStripMenuItem_Click(object sender, EventArgs e)
        {
            using (Joystick joy = new Joystick(sl160))
            {
                if (joy.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                {

                }
            }
        }

        private void lbllasterror_Click(object sender, EventArgs e)
        {
            sl160.priorSDK.Cmd("sl160.lasterror.clear", ref userRx);
        }

        private void previewOnToolStripMenuItem_CheckedChanged(object sender, EventArgs e)
        {
            if (previewOnToolStripMenuItem.Checked == true)
            {
                /* turn back on previewstate mode */
                sl160.priorSDK.Cmd("sl160.previewstate.set 0", ref userRx, false);
            }
            else
            {
                /* turn off previewstate mode */
                sl160.priorSDK.Cmd("sl160.previewstate.set -1", ref userRx, false);
            }

        }

        private void ReInitialiseToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (sl160.StateNotEquals(Prior.SL160_STATE_IDLE) || (mySoakState != SoakState.soakIdle))
            {
                MessageBox.Show("SL160 must be idle First", "Info ",
                                      MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            else
            {
                if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
                {
                    if (MessageBox.Show("Are you sure you want to Re-initialise?", "Initialise",
                                      MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
                    {
                        ReInitialise();
                    }
                }
            }
        }

        private void ReInitialise()
        {
            /* perform required initialisation of loader and stage
            * loader is initialised by DLL API call, stage/z is initialised by users application (this demo)
            * */
            using (initialise init = new initialise(sl160))
            {
                if (init.ShowDialog() != System.Windows.Forms.DialogResult.OK)
                {
                    this.Visible = true;
                    Disconnect();
                }
            }
        }

        private void btnStop_Click(object sender, EventArgs e)
        {
            /* emergency stop */
            sl160.priorSDK.Cmd("sl160.stop", ref userRx);
            StopSoak();
            if (MessageBox.Show("It is advisable to re-initialise after an emergency stop.\r\rDo you wish to Re-Initialise now?", "Initialise",
                                          MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
            {
                ReInitialise();
            }
        }

        private void ManualoolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (sl160.StateNotEquals(Prior.SL160_STATE_IDLE) || (mySoakState != SoakState.soakIdle))
            {

                MessageBox.Show("SL160 must be idle to allow manual move", "Info ",
                                      MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            else
            {
                /* allow manual move if idle and not soaking
                * */
                using (ManualMove move = new ManualMove(sl160))
                {
                    move.ShowDialog();
                }
            }
        }
    }
}
