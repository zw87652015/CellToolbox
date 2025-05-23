using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;

using System.Windows.Forms;

namespace SL160_LoaderDemo
{
   
    public class SL160
    {
        /* create a c# wrapper class for the Prior DLL */
        public SDK priorSDK = new SDK();

        public int maxApartments = 20;
        public int maxHotels = 2;
        public int sessionID = -1;

        public string[] lastErr = { "OK",   //  0                         
                                    "Err: NOT INITIALISED",  //1
                                    "Err: NOT SETUP", //2
                                    "Err: GRIPPER HOMING FAILED",//3
                                    "Err: INVALID HOTEL",//4
                                    "Err: INVALID PLATE",//5
                                    "",//6
                                    "Err: PLATE IN GRIPPER",//7
                                    "Err: PLATE ON STAGE",//8
                                    "Err: INVALID STATE CHANGE",//9
                                    "Err: HOTEL IN USE REMOVED",//10
                                    "Err: WRONG PLATESENSOR STATE", //11
                                    "Err: STAGE MOVED OFF LOAD POINT",//12
                                    "Err: COMMS ERROR", //13
                                    "Err: AXIS STALLED", //14
                                };

        public int currentRobotStatus { get; set; }
        public int currentRobotState { get; set; }
        public int lastRobotstate { get; set; }
        public int lastRobotStatus { get; set; }
        public int lastRobotErr { get; set; }
        public int previewState { get; set; }
        public int connectedState { get; set; }
        public int lastConnectedState { get; set; }

        public class CALIBRATION
        {
            public int TYPEMASK = 0x0F000000;
            public int NONE = 0x00000000;
            public int FIXED = 0x01000000;
            public int USER = 0x02000000;
            public int PRIOR = 0x03000000;
            public int HOTELCALIBRATED = 0x00000001;
            public int STAGECALIBRATED = 0x00000002;


            public int flags { get; set; }
        }


        public CALIBRATION calibration = new CALIBRATION();

        private int err;

        private string calibratedXYStagePosition = "";
        private string calibratedZStagePosition = "";

        public SL160()
        {
            currentRobotStatus = 0;
            currentRobotState = 0;
            lastRobotstate = 0;
            lastRobotStatus = 0;
            lastRobotErr = 0;
            previewState = 0;
            connectedState = 0;
            lastConnectedState = 0;
        }

        public int SaveCalibrationFlagsToController()
        {
            string userRx = "";

            return priorSDK.Cmd("sl160.calibration.flags.set " + calibration.flags.ToString(), ref userRx, false);
        }

        public int LoadCalibrationFlagsFromController()
        {
            string status = "";
            int err;

            calibration.flags = 0;

            if ((err = priorSDK.Cmd("sl160.calibration.flags.get", ref status, false)) == Prior.PRIOR_OK)
            {
                calibration.flags = Convert.ToInt32(status);
            }

            return calibration.flags;
        }

        public void ClearHotelCalibrationFlag()
        {
            calibration.flags &= ~calibration.HOTELCALIBRATED;
        }
        public void ClearStageCalibrationFlag()
        {
            calibration.flags &= ~calibration.STAGECALIBRATED;
        }
        public void ClearAllCalibrationFlags()
        {
            calibration.flags = 0;
        }

        public int HotelCalibrationDone()
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            calibration.flags |= calibration.HOTELCALIBRATED;

            /* this only sets the hotel calibration flags in the controller. They have to be saved to stage eeprom
             *  but that involves turning the motors off so we delay commit until calibration completed
             *  */
            err = priorSDK.Cmd("sl160.calibration.hotel.set", ref userRx, false);

            return err;
        }

        public int StageCalibrationDone()
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            calibration.flags |= calibration.STAGECALIBRATED;

            /* this only sets the stage calibration flags in the controller. They have to be saved to stage eeprom
             *  but that involves turning the motors off so we delay commit until calibration completed
             *  */
            err = priorSDK.Cmd("sl160.calibration.stage.set", ref userRx, false);

            return err;
        }

        public int SaveCalibrationToController()
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            /* writing to the eeprom on the stage takes several seconds and involves turning the 
             * motors off so we may lose stage position. This routine sets the controller cold start
             * flag so that on the next connect a full initialisation will occur.
             *  */
            err = priorSDK.Cmd("sl160.calibration.flags.save", ref userRx, false);

            return err;
        }

  
      
        private bool setFlags(int type)
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            calibration.flags &= ~(calibration.TYPEMASK);
            calibration.flags |= type;
            err = priorSDK.Cmd("sl160.calibration.flags.set " + calibration.flags.ToString(), ref userRx, false);

            if (err != Prior.PRIOR_OK)
                return false;
            else
                return true;
        }
        
        public bool SetCalibrationTypeFixed()
        {
           return setFlags(calibration.FIXED);
        }   
        
        public bool SetCalibrationTypeUser()
        {
           return setFlags(calibration.USER);
        }   
        
        public bool SetCalibrationTypePrior()
        {
           return setFlags(calibration.PRIOR);
        }

        public bool NoDeviceTypeSet()
        {
            if ((calibration.flags & (calibration.TYPEMASK)) == calibration.NONE)
                return true;
            else
                return false;
        }

        public bool IsFixedHeight()
        {
            if ((calibration.flags & (calibration.TYPEMASK)) == calibration.FIXED)
                return true;
            else
                return false;
        }

        public bool IsCustomerVariableHeight()
        {
            if ((calibration.flags & (calibration.TYPEMASK)) == calibration.USER)
                return true;
            else
                return false;
        }

        public bool IsPriorVariableHeight()
        {
            if ((calibration.flags & (calibration.TYPEMASK)) == calibration.PRIOR)
                return true;
            else
                return false;
        }


        public bool RequiresHotelCalibration()
        {
            if ((calibration.flags & calibration.HOTELCALIBRATED) != 0)
                return false;
            else
                return true;
        }
        
        public bool RequiresStageCalibration()
        {
            if ((calibration.flags & calibration.STAGECALIBRATED) != 0)
                return false;
            else
                return true;
        }

    

        public string GetLastErrorAsString(int err)
        {
            return lastErr[System.Math.Abs(err)];
        }

        public string StatusBitToString(int bit, string T, string F)
        {
            if ((currentRobotStatus & bit) == bit)
                return T;
            else
                return F;
        }

        public bool StatusBitIsSet(int bit)
        {
            if ((currentRobotStatus & bit) == bit)
                return true;
            else
                return false;
        }

        public bool StateEquals(int state)
        {
            if ((currentRobotStatus & Prior.SL160_STATE_STATEMASK) == state)
                return true;
            else
                return false;
        }

        public bool StateNotEquals(int state)
        {
            return !StateEquals(state);
        }

        public int GetStateFromStatus(int status)
        {
            return status & Prior.SL160_STATE_STATEMASK;
        }

        public string GetStateAsString(int majorState)
        {
            switch (majorState)
            {

                case Prior.SL160_STATE_UNKNOWN:
                    return "UNKNOWN";

                case Prior.SL160_STATE_SETUP:
                    return "SETUP";

                case Prior.SL160_STATE_INITIALISE:
                    return "INITIALISING";

                case Prior.SL160_STATE_STOP:
                    return "STOP";

                case Prior.SL160_STATE_IDLE:
                    return "IDLE";

                case Prior.SL160_STATE_TXF_TOSTAGE:
                    return "LOADING TRAY";

                case Prior.SL160_STATE_TXF_FROMSTAGE:
                    return "UNLOADING TRAY";

                case Prior.SL160_STATE_SCANHOTEL:
                    return "SCANNING HOTEL";

                case Prior.SL160_STATE_LOAD_HOTELS:
                    return "INSERTING HOTELS";

                case Prior.SL160_STATE_UNLOAD_HOTELS:
                    return "EJECTING HOTELS";

                default:
                    return "STATE_UNKNOWN";
            }
        }


        public void PollStatus()
        {
            string status = "";
            int err;

            if ((err = priorSDK.Cmd("sl160.status.get", ref status, false)) == Prior.PRIOR_OK)
            {
                currentRobotStatus = Convert.ToInt32(status);
            }
        }

        public void UpdateLastError()
        {
            string userRx = "";
            int err;

            if ((err = priorSDK.Cmd("sl160.lasterror.get", ref userRx, false)) == Prior.PRIOR_OK)
            {
                lastRobotErr = Convert.ToInt32(userRx);
            }
        }

        public int StageBusy()
        {
            string userRx = "";
            int err;

            if ((err = priorSDK.Cmd("controller.stage.busy.get", ref userRx,false)) != Prior.PRIOR_OK)
            {
                return 0;
            }
            else
                return Convert.ToInt32(userRx);
        }

        public int ZBusy()
        {
            string userRx = "";

            if ((err = priorSDK.Cmd("controller.z.busy.get", ref userRx,false)) != Prior.PRIOR_OK)
            {
                return 0;
            }
            else
                return Convert.ToInt32(userRx);
        }

        public int WaitUntilStageIdle()
        {
            do
            {
                Application.DoEvents();
                Thread.Sleep(100);
            }
            while (StageBusy() != 0);

            return err;
        }

        public void WaitUntilZIdle()
        {
            do
            {
                Application.DoEvents();
                Thread.Sleep(100);
            }
            while (ZBusy() != 0);
        }

        public int StageToOpenClampPosition()
        {
            string userRx = "";
            int err;

            /* move quickly to close to left limit switch and close to Y axis aligment with stage for openstand system
             * */
            if ((err = priorSDK.Cmd("controller.stage.goto-position 100000 76500", ref userRx, false)) != Prior.PRIOR_OK)
            {
                return err;
            }

            WaitUntilStageIdle();

            /* move slowly to stage left limit switch
             * */
            if ((err = priorSDK.Cmd("controller.stage.move-at-velocity " +
                                       (2000).ToString() + " " + (0).ToString(), ref userRx,false)) != Prior.PRIOR_OK)
            {
                return err;
            }

            WaitUntilStageIdle();

            /* back off 5mm top supposedly open clamp fully.
             * */
            if ((err = priorSDK.Cmd("controller.stage.move-relative " +
                                       (-500).ToString() + " " + (0).ToString(), ref userRx,false)) != Prior.PRIOR_OK)
            {
                return err;
            }

            WaitUntilStageIdle();

            return 0;
        }

        public int InitStage()
        {
            int flags;
            string userRx = "";
            int err;

            /* check warm start flags */
            if ((err = priorSDK.Cmd("controller.flag.get", ref userRx,false)) != Prior.PRIOR_OK)
            {
                return err;
            }

            /* this is an arbitrary bit of the user ProScan3 FLAG to determine whther cold start or not.
            * */
            const int PS3warmStartFlag = (int)0x1000;

            /* warm start flags returned in hex string format */
            flags = Convert.ToInt32(userRx, 16);

           
            if ((flags & PS3warmStartFlag) != PS3warmStartFlag)
            {
                /* if Prior in charge of the stage height, ie it attached to an FB20X or the like we should initialise Z
                 * first
                 * */
                if (IsPriorVariableHeight())
                {
                    /* do Z initilaisation, this will be for a system like and FB20X controlled by PS3
                     * */

                    if ((err = priorSDK.Cmd("controller.z.move-at-velocity " + (-5000).ToString() , ref userRx, false)) != Prior.PRIOR_OK)
                    {
                        return err;
                    }

                    WaitUntilZIdle();


                    /* set temp zero pos */
                    if ((err = priorSDK.Cmd("controller.z.position.set ", ref userRx, false)) != Prior.PRIOR_OK)
                    {
                        return err;
                    }

                    /* move off slightly */
                    if ((err = priorSDK.Cmd("controller.z.goto-position 10000", ref userRx, false)) != Prior.PRIOR_OK)
                    {
                        return err;
                    }

                    WaitUntilZIdle();

                    /* slow into limits */
                    if ((err = priorSDK.Cmd("controller.z.move-at-velocity " + (-500).ToString() , ref userRx, false)) != Prior.PRIOR_OK)
                    {
                        return err;
                    }

                    WaitUntilZIdle();

                    /* set temp zero pos */
                    if ((err = priorSDK.Cmd("controller.z.position.set 0", ref userRx, false)) != Prior.PRIOR_OK)
                    {
                        return err;
                    }

                    /* move off slightly */
                    if ((err = priorSDK.Cmd("controller.z.goto-position 10000", ref userRx, false)) != Prior.PRIOR_OK)
                    {
                        return err;
                    }

                    WaitUntilZIdle();

                    /* set real zero co-ordinates to avoid having to hit switch again */
                    if ((err = priorSDK.Cmd("controller.z.position.set 0", ref userRx, false)) != Prior.PRIOR_OK)
                    {
                        return err;
                    }
                }

                /* do stage initialisation, independent of stage orientation as that already been setup 
                 * goto limits first
                 */

                if ((err = priorSDK.Cmd("controller.stage.move-at-velocity " +
                                                (-10000).ToString() + " " + (-10000).ToString(), ref userRx, false)) != Prior.PRIOR_OK)
                {
                    return err;
                }

                WaitUntilStageIdle();


                /* set temp zero pos */
                if ((err = priorSDK.Cmd("controller.stage.position.set 0 0", ref userRx, false)) != Prior.PRIOR_OK)
                {
                    return err;
                }

                /* move off slightly */
                if ((err = priorSDK.Cmd("controller.stage.goto-position 1000 1000", ref userRx, false)) != Prior.PRIOR_OK)
                {
                    return err;
                }

                WaitUntilStageIdle();

                /* slow into limits */
                if ((err = priorSDK.Cmd("controller.stage.move-at-velocity " +
                                               (-500).ToString() + " " + (-500).ToString(), ref userRx, false)) != Prior.PRIOR_OK)
                {
                    return err;
                }

                WaitUntilStageIdle();

                /* set temp zero pos */
                if ((err = priorSDK.Cmd("controller.stage.position.set 0 0", ref userRx, false)) != Prior.PRIOR_OK)
                {
                    return err;
                }

                /* move off slightly */
                if ((err = priorSDK.Cmd("controller.stage.goto-position 1000 1000", ref userRx, false)) != Prior.PRIOR_OK)
                {
                    return err;
                }

                WaitUntilStageIdle();

                /* set real zero co-ordinates to avoid having to hit switch again */
                if ((err = priorSDK.Cmd("controller.stage.position.set 0 0", ref userRx, false)) != Prior.PRIOR_OK)
                {
                    return err;
                }

            }

            flags |= PS3warmStartFlag;

            if ((err = priorSDK.Cmd("controller.flag.set " + flags.ToString("X"), ref userRx, false)) != Prior.PRIOR_OK)
            {
                return err;
            }

            return Prior.PRIOR_OK;
        }

    

        private int mmToCounts(int axis, double mm)
        {
            int counts = 0;
            switch (axis)
            {
                case Prior.SL160_HSM:
                {
                    //proto has 500 line encoder, 2000 counts/rev, 6mm pitch screw
                    counts = Convert.ToInt32((2000.0 * mm) / 6.0);
                    break;
                }

                case Prior.SL160_HLM:
                {
                    // proto has 500 line encoder, 2000 counts/rev, 2mm pitch screw
                    counts = Convert.ToInt32((2000.0 * mm) / 2.0);
                    break;
                }

                case Prior.SL160_STM:
                {
                    // proto has 500 line encoder, 2000 counts/rev, 6mm pitch screw
                    counts = Convert.ToInt32((2000.0 * mm) / 6.0);
                    break;
                }
            }

            return counts;
        }

        public int AxisMoveTo(int axis, int pos)
        {
            int err;

            string userRx = "";
            err = priorSDK.Cmd("sl160.axis.goto " + axis.ToString() + " " + pos.ToString(), ref userRx, false);

            return err;
        }

        public int AxisJogBy(int axis, int counts)
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            priorSDK.Cmd("sl160.axis.busy.get " + axis.ToString(), ref userRx,false);

            if (userRx.Equals("0") == true)
            {
                int pos = 0;

                if ((err = priorSDK.Cmd("sl160.axis.position.get " + axis.ToString(), ref userRx,false)) == Prior.PRIOR_OK)

                pos += Convert.ToInt32(userRx);
                pos += counts;

                err = AxisMoveTo(axis, pos);
            }

            return err; 
        }

        public int AxisMoveAtVelocity(int axis, double counts)
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            err = priorSDK.Cmd("sl160.axis.move-at-velocity " + axis.ToString() + " " + counts.ToString(), ref userRx,false);
            return err;
        }

        private int WaitAxisNotBusy(int axis)
        {
            int busy = 0;
            string userRx = "";
            int err = Prior.PRIOR_OK;

            do
            {
                Thread.Sleep(100);

                if ((err = priorSDK.Cmd("sl160.axis.busy.get " + axis.ToString(), ref userRx, false)) != Prior.PRIOR_OK)
                    return 0;

                busy = Convert.ToInt32(userRx);
            }
            while (busy != 0);

            return busy;
        }

        public int HotelLiftTo(double mm)
        {
            int err = Prior.PRIOR_OK;

            /* lift to required height mm 
             * */
            if ((err = AxisMoveTo(Prior.SL160_HLM, mmToCounts(Prior.SL160_HLM, mm))) == Prior.PRIOR_OK)
            {
                err = WaitAxisNotBusy(Prior.SL160_HLM);
            }

            return err;
        }
        
        public int HotelLiftBy(double mm)
        {
            int err = Prior.PRIOR_OK;

            /* jog hotel height by mm
             * */
            if ((err = AxisJogBy(Prior.SL160_HLM, mmToCounts(Prior.SL160_HLM, mm))) == Prior.PRIOR_OK)
            {
                err = WaitAxisNotBusy(Prior.SL160_HLM);
            }

            return err;
        }

      

        public int HotelShuttleMoveBy(double jogmm)
        {
            int err = Prior.PRIOR_OK;

            if ((err = AxisJogBy(Prior.SL160_HSM, mmToCounts(Prior.SL160_HSM, jogmm))) == Prior.PRIOR_OK)
            {
                err = WaitAxisNotBusy(Prior.SL160_HSM);
            }

            return err;
        }

        public int StageShuttleMoveTo(double pos)
        {
            int err = Prior.PRIOR_OK;

            if ((err = AxisMoveTo(Prior.SL160_STM, mmToCounts(Prior.SL160_STM, pos))) == Prior.PRIOR_OK)
            {
                err = WaitAxisNotBusy(Prior.SL160_STM);
            }

            return err;
        }

        public int StageShuttleMoveBy(double pos)
        {
            int err = Prior.PRIOR_OK;

            if ((err = AxisJogBy(Prior.SL160_STM, mmToCounts(Prior.SL160_STM, pos))) == Prior.PRIOR_OK)
            {
                WaitAxisNotBusy(Prior.SL160_STM);
            }

            return err;
        }

        public int STM_MoveAtVelocity(double vel)
        {
            int err = Prior.PRIOR_OK;

            err = AxisMoveAtVelocity(Prior.SL160_STM, mmToCounts(Prior.SL160_STM, vel));

            return err;
        }

        public int HSM_MoveAtVelocity(double vel)
        {
            int err = Prior.PRIOR_OK;

            err = AxisMoveAtVelocity(Prior.SL160_HSM, mmToCounts(Prior.SL160_HSM, vel));

            return err;
        }

        public int HLM_MoveAtVelocity(double vel)
        {
            int err = Prior.PRIOR_OK;

            err = AxisMoveAtVelocity(Prior.SL160_HLM, mmToCounts(Prior.SL160_HLM, vel));

            return err;
        }
       

        public int InitLoader()
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            /* start the robot initialisation */
            if ((err = priorSDK.Cmd("sl160.initialise", ref userRx,false)) != Prior.PRIOR_OK)
            {
                return err;
            }


            /* wait until initialisation complete by checking status 
             * minimum initialistaion will retract the STM allowing recovery from a shutdown that 
             * potentially may have left a tray or the STM partly in an apartment
             * Internally the sl160.initialise also checks the controller.flag status to 
             * determine warm or cold start conditions
             */
            do
            {
                // TODO: add timeout check here to try to catch some obviously broken sl160 drive functions
                Thread.Sleep(100);
                PollStatus();
            }
            while (StateEquals(Prior.SL160_STATE_INITIALISE));

            return err;
        }

        public int EjectHotels()
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            if ((err = priorSDK.Cmd("sl160.unloadhotels", ref userRx,false)) == Prior.PRIOR_OK)
            {
                /* wait until unload complete by checking status */
                do
                {
                    PollStatus();
                    Application.DoEvents();
                    Thread.Sleep(200);
                }
                while (StateNotEquals(Prior.SL160_STATE_IDLE));
            }
            else
            {
                MessageBox.Show("Cannot eject hotel (" + err.ToString() + ")", "Error",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
            }

            return err;
        }

        public int LoadHotels()
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            if ((err = priorSDK.Cmd("sl160.loadhotels", ref userRx, false)) == Prior.PRIOR_OK)
            {
                /* wait until unload complete by checking status */
                do
                {
                    PollStatus();
                    Application.DoEvents();
                    Thread.Sleep(200);
                }
                while (StateNotEquals(Prior.SL160_STATE_IDLE));
            }
            else
            {
                MessageBox.Show("Cannot load hotel (" + err.ToString() + ")", "Error",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
            }

            return err;
        }

        public bool Apartment1and20Occupied(int hotel)
        {
            bool ok = true;

            if ((ok = TrayFitted(hotel, 1)) == false)
            {
                MessageBox.Show("Tray in Apartment 1 not detected!", "Error",
                           MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            else
            if ((ok = TrayFitted(hotel, 20)) == false)
            {
                MessageBox.Show("Tray in Apartment 20 not detected!", "Error",
                                            MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            else
            {
                int tray;

                for (tray = 2; tray < 20; tray++)
                {
                    if (TrayFitted(hotel, tray) == true)
                    {
                        MessageBox.Show("Tray in Apartment " + tray + " detected!", "Error",
                                              MessageBoxButtons.OK, MessageBoxIcon.Error);
                        ok = false;
                        break;
                    }
                }

            }

            return ok ;
        }

        public int ScanHotel(int hotel)
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            if ((err = priorSDK.Cmd("sl160.scanhotel " + hotel.ToString(), ref userRx,false)) == Prior.PRIOR_OK)
            {
                /* wait until scan complete by checking status */
                do
                {
                    PollStatus();
                    Application.DoEvents();
                    Thread.Sleep(200);
                }
                while (StateNotEquals(Prior.SL160_STATE_IDLE));
            }
            else
            {
                MessageBox.Show("Cannot load hotel (" + err.ToString() + ")", "Error",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
            }

            return err;
        }
        
        public bool TrayFitted(int hotel,int apartment)
        {
            string userRx = "";
            int err = Prior.PRIOR_OK;

            if ((err = priorSDK.Cmd("sl160.trayfitted.get " + hotel.ToString() + " " + apartment.ToString(), ref userRx))
                                                                == Prior.PRIOR_OK)
            {
                if (userRx.Equals("1") == true)
                    return true;
                else
                    return false;
            }

            return false;
        }


        public bool HotelFitted(int hotel )
        {
            string userRx = "";

            if ((err = priorSDK.Cmd("sl160.hotelfitted.get " + hotel.ToString(), ref userRx, false)) == Prior.PRIOR_OK)
            {
                if (userRx.Equals("1") == true)
                    return true;
                else
                    return false;
            }    
            return false;
        }

        public bool TrayOnStage()
        {
            PollStatus();
            return StatusBitIsSet(Prior.SL160_LOADER_TRAYONSTAGE);
        }

        /* XYZ to load position actually performed by loader automatically when scanning or transferring
        * IMPORTANT that user performs their own esacpe objectives routine and position to objectives after 
        * scanning/loading/unloading etc.
        * */
        public int LoadStageXYZCalibration()
        {
            string userRx = "";

            if ((err = priorSDK.Cmd("sl160.calibration.stagexy.get", ref userRx, false)) == Prior.PRIOR_OK)
            {
                calibratedXYStagePosition = userRx;
            } 
            else
            return err;


            if ((err = priorSDK.Cmd("sl160.calibration.stagez.get", ref userRx, false)) == Prior.PRIOR_OK)
            {
                calibratedZStagePosition = userRx;
            } 
   

            return err;
        }

        /* XYZ to load position actually performed by loader automatically when scanning or transferring
         * IMPORTANT that user performs their own esacpe objectives routine and position to objectives after 
         * scanning/loading/unloading etc.
         * */
        public int PositionStageToLoad()
        {
            string userRx = "";
            int err = 0;

            err = priorSDK.Cmd("controller.stage.goto-position " + calibratedXYStagePosition, ref userRx, false);

            return err;
        }
    }
}
