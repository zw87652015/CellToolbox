using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading;
using System.Windows.Forms;

using SL160_LoaderDemo.Properties;

namespace SL160_LoaderDemo
{
    public partial class Form1 : Form
    {

        public bool pollStatus = true;
        string statusRx = "";

        private void RobotStatusHandling_DoWork(object sender, DoWorkEventArgs e)
        {
            try
            {
                while (true)
                {
                    Thread.Sleep(200);

                    if (pollStatus)
                    {
                        sl160.PollStatus();

                        RobotStatusHandling.ReportProgress(1);
                    }
                }
            }
            catch (Exception rsh)
            {
                /* ignore */
                string s = rsh.Message;
            }
        }



        private void HandleTiming()
        {
            sl160.currentRobotState = sl160.GetStateFromStatus(sl160.currentRobotStatus);

            if (sl160.currentRobotState != sl160.lastRobotstate)
            {
                if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
                {
                    myStopWatch.Stop();
                    long elapsed = myStopWatch.ElapsedMilliseconds / 1000;
                    lbltime.Text = elapsed.ToString() + "s";
                }
                else
                {
                    myStopWatch.Restart();
                }

                sl160.lastRobotstate = sl160.currentRobotState;
            }
        }

       

        private void UpdateSL160StatusFlags()
        {

            if (sl160.currentRobotStatus != sl160.lastRobotStatus)
            {
               if (sl160.StatusBitIsSet(Prior.SL160_LOADER_ERROR))
                {
                    lblError.Text = "ERROR";
                    lblError.BackColor = Color.Red;
                }
                else
                {
                    lblError.Text = "";
                    lblError.BackColor = SystemColors.Control;
                }

               

                /* display status bits */
               lblEject.Text = sl160.StatusBitToString(Prior.SL160_LOADER_HOTELEJECTED, "HOTELS EJECTED", "HOTELS INSERTED");

               if (sl160.StatusBitIsSet(Prior.SL160_LOADER_HOTELEJECTED))
               {
                   lblEject.BackColor = Color.Yellow; 
                   btnEjectHotels.Enabled = false;
                   btnToHotel.Enabled = false;
                   btnToStage.Enabled = false;
                   btnLoadHotels.Enabled = true;
               }
               else
               {
                   lblEject.BackColor = Color.LightGreen; 
                   btnEjectHotels.Enabled = true;
                   btnToHotel.Enabled = true;
                   btnToStage.Enabled = true;
                   btnLoadHotels.Enabled = false; ;
               }


               lblNotInitialised.Text = sl160.StatusBitToString(Prior.SL160_LOADER_NOTINITIALISED, "NOT INITIALISED", "");
               lblNotSetup.Text = sl160.StatusBitToString(Prior.SL160_LOADER_NOTSETUP, "NOT SETUP", "");

               if (sl160.StatusBitIsSet(Prior.SL160_LOADER_NOTIDLE))
                {
                     lblNotIdle.Text = "ACTIVE";
                     lblNotIdle.BackColor = Color.Yellow;
                }
                else
                {
                    lblNotIdle.Text = "IDLE";
                    lblNotIdle.BackColor =  SystemColors.Control;
                }

               lblCassetteNotScanned.Text = sl160.StatusBitToString(Prior.SL160_LOADER_HOTELNOTSCANNED, "NOT SCANNED", "");
               lblInvalidSlide.Text = sl160.StatusBitToString(Prior.SL160_LOADER_INVALIDTRAY, "INVALID TRAY", "");
               lblInvalidCassette.Text = sl160.StatusBitToString(Prior.SL160_LOADER_INVALIDHOTEL, "INVALID HOTEL", "");

               if (sl160.StatusBitIsSet(Prior.SL160_LOADER_TRAYONSTAGE))
                {
                    lblSlideOnStage.Text = "TRAY ON STAGE";
                    lblSlideOnStage.BackColor = Color.LightGreen;
                }
                else
                {
                    lblSlideOnStage.Text = "";
                    lblSlideOnStage.BackColor = SystemColors.Control;
                }

               lblCommsError.Text = sl160.StatusBitToString(Prior.SL160_LOADER_COMMSERROR, "COMMS ERR", "");
               lblSlideSensorError.Text = sl160.StatusBitToString(Prior.SL160_LOADER_TRAYSENSORERROR, "TRAY SENSOR ERR", "");

               if (sl160.StatusBitIsSet(Prior.SL160_LOADER_AXISSTALLED))
                {
                    int axis;

                    if ((err = sl160.priorSDK.Cmd("sl160.stalledaxis.get", ref statusRx, false)) != Prior.PRIOR_OK)
                    {
                        return;
                    }

                    axis = Convert.ToInt32(statusRx);

                    if (axis == 1)
                        lblStallError.Text = "X AXIS STALLED";
                    if (axis == 2)
                        lblStallError.Text = "Y AXIS STALLED";
                    if (axis == 3)
                        lblStallError.Text = "Z AXIS STALLED";
                }
                else
                    lblStallError.Text = "";
            }

            lblstate.Text = sl160.GetStateAsString(sl160.GetStateFromStatus(sl160.currentRobotStatus));

            lbllasterror.Text = sl160.GetLastErrorAsString(sl160.lastRobotErr);

            sl160.lastRobotStatus = sl160.currentRobotStatus;

            if ((err = sl160.priorSDK.Cmd("sl160.previewstate.get", ref statusRx, false)) == Prior.PRIOR_OK)
            {
                sl160.previewState = Convert.ToInt32(statusRx);

                btnPreview.Text = "Preview " + sl160.previewState.ToString();

                if (sl160.previewState < 1)
                {
                    btnPreview.Enabled = false;
                }
                else
                {
                    btnPreview.Enabled = true;
                }
            }
        }

        private void RobotStatusHandling_ProgressChanged(object sender, ProgressChangedEventArgs e)
        {

            if ((sl160.currentRobotStatus & Prior.SL160_LOADER_NOTCONNECTED) != 0)
                sl160.connectedState = 0;
            else
                sl160.connectedState = 1;

            if (sl160.connectedState != sl160.lastConnectedState)
            {
                sl160.lastConnectedState = sl160.connectedState;

                if (sl160.connectedState == 0)
                {
                    grpAction.Enabled = false;

                    connectToolStripMenuItem.Text = "Connect";

                    editINIToolStripMenuItem.Enabled = false;
                    optionsToolStripMenuItem.Enabled = false;
                    ManualoolStripMenuItem.Enabled = false;
                    grpHotel1.Enabled = false;
                    grpHotel2.Enabled = false;

                    lblNotConnected.Text = "NOT CONNECTED";
                    lblNotConnected.BackColor = Color.Yellow;

                }
                else
                {
                    lblNotConnected.Text = "CONNECTED";
                    lblNotConnected.BackColor = Color.LightGreen;
                    connectToolStripMenuItem.Text = "DisConnect";
                    editINIToolStripMenuItem.Enabled = true;
                    optionsToolStripMenuItem.Enabled = true;
                    ManualoolStripMenuItem.Enabled = true;
                }
            }

            HandleTiming();

          

            /* check for hotel fitted status */
            if ((err = sl160.priorSDK.Cmd("sl160.hotelfitted.get 1", ref statusRx,false)) == Prior.PRIOR_OK)
            {
                if (statusRx.Equals("1") == true)
                {
                    if (grpHotel1.Enabled == false)
                    {
                        grpHotel1.Enabled = true;
                    }
                }
                else
                {
                    if (grpHotel1.Enabled == true)
                    {
                        grpHotel1.Enabled = false;
                    }
                }
            }    
            
            /* check for hotel fitted status */
            if ((err = sl160.priorSDK.Cmd("sl160.hotelfitted.get 2", ref statusRx,false)) == Prior.PRIOR_OK)
            {
                if (statusRx.Equals("1") == true)
                {
                    if (grpHotel2.Enabled == false)
                    {
                        grpHotel2.Enabled = true;
                    }
                }
                else
                {
                    if (grpHotel2.Enabled == true)
                    {
                        grpHotel2.Enabled = false;
                    }
                }
            }


            sl160.UpdateLastError();

            UpdateSL160StatusFlags();

            /* keep track of plates */
          
            int tray = 0;

            for (tray = 0; tray < 20; tray++)
            {
                if (grpHotel1.Enabled == true)
                {
                    if ((err = sl160.priorSDK.Cmd("sl160.trayfitted.get 1 " + (tray + 1).ToString(), ref statusRx, false)) == Prior.PRIOR_OK)
                    {
                        if (statusRx.Equals("1") == true)
                        {
                            if (hotel1[tray].BackColor != Color.LightGreen)
                                hotel1[tray].BackColor = Color.LightGreen;
                        }
                        else
                        {
                            if (hotel1[tray].BackColor != SystemColors.Control)
                                hotel1[tray].BackColor = SystemColors.Control;
                        }
                    }
                }
                else
                {
                    if (hotel1[tray].BackColor != SystemColors.Control)
                        hotel1[tray].BackColor = SystemColors.Control;
                }

                if (grpHotel2.Enabled == true)
                {
                    if ((err = sl160.priorSDK.Cmd("sl160.trayfitted.get 2 " + (tray + 1).ToString(), ref statusRx, false)) == Prior.PRIOR_OK)
                    {
                        if (statusRx.Equals("1") == true)
                        {
                            if (hotel2[tray].BackColor != Color.LightGreen)
                                hotel2[tray].BackColor = Color.LightGreen;
                        }
                        else
                        {
                            if (hotel2[tray].BackColor != SystemColors.Control)
                                hotel2[tray].BackColor = SystemColors.Control;
                        }
                    }
                }
                else
                {
                    if (hotel2[tray].BackColor != SystemColors.Control)
                        hotel2[tray].BackColor = SystemColors.Control;
                }
            }

            sl160.lastRobotStatus = sl160.currentRobotStatus;

            DoSoak();

            if (openStandFitted)
                UpDateOpenStand();
        }

        enum SoakState
        {
            soakIdle,
            soakStart,
            soakFindNextTray,
            soakTransferToStage,

            soakPreview1,
            soakPreview2, 
            soakPreview3,
            soakPreview4,
            soakTrayLoaded,

            soakDoStageRaster,
            soakTransferToHotel,

            soakScan1,
            soakScan2
        };

        SoakState mySoakState = SoakState.soakIdle;
        int soakTray = 1;
        int soakCount = 0;

        List<string> raster = new List<string>{ 
                                "50000 50000", 
                                "40000 50000",
                                "40000 40000",
                                "50000 40000" };
        int rasterIndex = 0;

        private void StartSoak()
        {   
            /* start a soak transferring available trays between hotel and stage and back
             * */
            mySoakState = SoakState.soakStart;
            soakCount = 0;
            grpAction.Enabled = false;
            grpHotel1.Enabled = false;
            userRequest = transferType.transferNone;
        }

        private void StartScanSoak()
        {
            /* start a soak scanning only hotel apartments. 
             * */
            mySoakState = SoakState.soakScan1; 
            soakCount = 0;
            grpAction.Enabled = false;
            grpHotel1.Enabled = false;
            userRequest = transferType.transferNone;
        }
          
        private void StopSoak()
        {
            /* stop any active soak 
             * */
            mySoakState = SoakState.soakIdle;
            grpAction.Enabled = true;
            grpHotel1.Enabled = true;
            doSoakToolStripMenuItem.Checked = false;
            scanOnlySoakToolStripMenuItem.Checked = false;
            sl160.priorSDK.Cmd("controller.stage.joyxyz.on", ref userRx, false);
        }

        private string GetHotelAndTray(int tray)
        {
            if (tray <= 20)
                return "1 " + tray.ToString();
            else
                return "2 " + (tray - 20).ToString();
        }

        private void AquireImage()
        {
            /* Hook for user based objective image aquisition */
        }

        private void AquirePreviewImage()
        {
            /* Hook for user based preview image aquisition */
        }

   
        private void DoSoak()
        {
            if (mySoakState != SoakState.soakIdle)
            {
                if (sl160.StatusBitIsSet(Prior.SL160_LOADER_ERROR))
                {
                    /* cancel the soak if an error is raised */
                    StopSoak();
                }
            }

            /* state machine for soak test */
            switch (mySoakState)
            {
                case SoakState.soakIdle:
                {
                    soakTray = 0;
                    break;
                }

                case SoakState.soakStart:
                {
                    /* cycle aound the known fitted trays in the hotels 
                     */
                    mySoakState = SoakState.soakFindNextTray;
                   
                    break;
                }

                case SoakState.soakFindNextTray:
                {
                    /* wait for loader to be idle 
                     */
                    if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
                    {
                        do
                        {
                            lblSoakCount.Text = soakCount.ToString();

                            soakTray++;
                            if (soakTray > 40)
                                soakTray = 1;

                            if ((err = sl160.priorSDK.Cmd("sl160.trayfitted.get " + GetHotelAndTray(soakTray), ref statusRx, false)) != Prior.PRIOR_OK)
                            {
                                StopSoak();
                                return;
                            }
                        }
                        while (statusRx.Equals("0"));

                        mySoakState = SoakState.soakTransferToStage;
                    }

                    break;
                }

                case SoakState.soakTransferToStage:
                {
                    if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
                    {
                        if ((err = sl160.priorSDK.Cmd("sl160.movetostage "
                                                 + GetHotelAndTray(soakTray), ref statusRx, false)) == Prior.PRIOR_OK)
                        {
                            /* dll will set the previewstate from zero to preview station number when STM is ready 
                             */
                            if (previewOnToolStripMenuItem.Checked == true)
                                mySoakState = SoakState.soakPreview1;
                            else
                                mySoakState = SoakState.soakTrayLoaded;
                        }
                        else
                        {
                            StopSoak();
                            return;
                        }
                    }

                    break;
                }

                case SoakState.soakPreview1:
                {
                    if (sl160.previewState == 1)
                    {
                        /* ASSERT: we have arrived at the first preview station, this would be the hook to add your preview capture
                         * solution ie webcam image capture etc. This comment also applies to preview station 2/3/4 below.
                         * 
                         * NOTE: it is *NOT* allowed to move the stage at this point as the tray will still be partially in the hotel.
                         *       if you want to preview scan with a low mag objective then do that when the tray is fully loaded 
                         *       you *MUST* index through these preview states even if you dont image each slide.
                         *       
                         * NEW:  preview can now be turned off completely by  command "sl160.previewstate.set -1"
                         */

                        AquirePreviewImage();

                        /* signal loader to continue */
                        sl160.priorSDK.Cmd("sl160.previewstate.set 0", ref statusRx, false);
                        mySoakState = SoakState.soakPreview2;
                    }

                    break;
                }

                case SoakState.soakPreview2:
                {
                    if (sl160.previewState == 2)
                    {
                        AquirePreviewImage();

                        /* signal loader to continue */
                        sl160.priorSDK.Cmd("sl160.previewstate.set 0", ref statusRx, false);
                        mySoakState = SoakState.soakPreview3;
                    }

                    break;
                }

                case SoakState.soakPreview3:
                {
                    if (sl160.previewState == 3)
                    {
                        AquirePreviewImage();

                        /* signal loader to continue */
                        sl160.priorSDK.Cmd("sl160.previewstate.set 0", ref statusRx, false);
                        mySoakState = SoakState.soakPreview4;
                    }

                    break;
                }

                case SoakState.soakPreview4:
                {
                    if (sl160.previewState == 4)
                    {
                        AquirePreviewImage();

                        /* signal loader to continue */
                        sl160.priorSDK.Cmd("sl160.previewstate.set 0", ref statusRx, false);
                        mySoakState = SoakState.soakTrayLoaded;
                    }

                    break;
                }

                case SoakState.soakTrayLoaded:
                {
                    if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
                    {
                        /* ASSERT: tray loaded - no need to check if tray there as soak would abort if error raised */
                        if (stageRasterEnabledToolStripMenuItem.Checked == false)
                        {
                            /* dont scan the slides, just put the tray back, 
                             */
                            mySoakState = SoakState.soakTransferToHotel;
                        }
                        else
                        {
                            rasterIndex = 0;

                            /* start move to first position in our raster pattern. This is very much simplified here as a group of points
                             * purely for use as an example only. Any real system would have probably constructed a scan pattern(s) based
                             * on the preview image. Also a real application would have to control focus and manage objective escape sequence
                             */

                            if ((err = sl160.priorSDK.Cmd("controller.stage.goto-position " + raster[rasterIndex], ref userRx)) == Prior.PRIOR_OK)
                            {
                                mySoakState = SoakState.soakDoStageRaster;
                            }
                            else
                            {
                                StopSoak();
                                return;
                            }
                        }
                    }
                    break;
                }

                case SoakState.soakDoStageRaster:
                {
                    if (sl160.StageBusy() == 0)
                    {
                        /* ASSERT: stage movement stopped, should be at rasterIndex position. 
                         */
                        AquireImage();

                        rasterIndex++;

                        if (rasterIndex == raster.Count)
                        {
                            /* scan finished */
                            mySoakState = SoakState.soakTransferToHotel;
                        }
                        else
                        {
                            if ((err = sl160.priorSDK.Cmd("controller.stage.goto-position " + raster[rasterIndex], ref userRx)) == Prior.PRIOR_OK)
                            {
                               /* stay in this state waiting for completed move */
                            }
                            else
                            {
                                StopSoak();
                                return;
                            }
                        }
                    }

                    break;
                }

                case SoakState.soakTransferToHotel:
                {
                    /* ASSERT: stage and loader are idle
                     */
                    if ((err = sl160.priorSDK.Cmd("sl160.movetohotel "
                                            + GetHotelAndTray(soakTray), ref statusRx, false)) == Prior.PRIOR_OK)
                    {
                        soakCount++;
                        mySoakState = SoakState.soakFindNextTray;
                    }
                    else
                    {
                        StopSoak();
                        return;
                    }

                    break;
                }

                /* hotel soak scan requires both hotels to be fitted, else the soak aborts. It then cycles indefinetly scanning
                 * each hotel in turn, execising the lifting/swapping hotels functions of the loader
                 */
                case SoakState.soakScan1:
                {
                    if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
                    {
                        if ((err = sl160.priorSDK.Cmd("sl160.hotelfitted.get 1", ref userRx, false)) != Prior.PRIOR_OK)
                        {
                            StopSoak();
                            return;
                        }
                        else
                        {
                            if (userRx.Equals("1") == true)
                            {
                                if ((err = sl160.priorSDK.Cmd("sl160.scanhotel 1", ref userRx, false)) == Prior.PRIOR_OK)
                                {
                                    soakCount++;
                                    lblSoakCount.Text = soakCount.ToString();
                                    mySoakState = SoakState.soakScan2;
                                }
                                else
                                {
                                    StopSoak();
                                    return;
                                }
                            }
                            else
                                mySoakState = SoakState.soakScan2;
                        }
                    }

                    break;
                }

                case SoakState.soakScan2:
                {
                    if (sl160.StateEquals(Prior.SL160_STATE_IDLE))
                    {
                        if ((err = sl160.priorSDK.Cmd("sl160.hotelfitted.get 2", ref userRx, false)) != Prior.PRIOR_OK)
                        {
                            StopSoak();
                            return;
                        }
                        else
                        {
                            if (userRx.Equals("1") == true)
                            {
                                if ((err = sl160.priorSDK.Cmd("sl160.scanhotel 2", ref userRx, false)) == Prior.PRIOR_OK)
                                {
                                    soakCount++;
                                    lblSoakCount.Text = soakCount.ToString();
                                    mySoakState = SoakState.soakScan1;
                                }
                                else
                                {
                                    StopSoak();
                                    return;
                                }
                            }
                            else
                                mySoakState = SoakState.soakScan1;
                        }
                    }

                    break;
                }
            }
        }
    }
}