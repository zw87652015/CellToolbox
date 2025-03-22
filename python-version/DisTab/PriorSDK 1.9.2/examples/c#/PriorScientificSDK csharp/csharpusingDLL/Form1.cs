/**
 * @file    csharpusingDLL
 * @date    5/5/2020
 * @brief   This project contains example source for using PriorSDK
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
 * */
 
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

/* This is just a quick simple hack to show principle of using PriorSDK. I have ommited much error checking etc
 * for the sake of, hopefully, clarity
 */

namespace csharpusingDLL
{
    public partial class Form1 : Form
    {

        int err;
        int sessionID = -1;

        string userRx = "";
        StringBuilder dllVersion = new StringBuilder();

        /* create a c# wrapper class for the Prior DLL */
        SDK priorSDK = new SDK();

        public Form1()
        {
            InitializeComponent();
        }



        private void Form1_Load(object sender, EventArgs e)
        {
            /* get the version number of the dll */
            if ((err = priorSDK.GetVersion(dllVersion)) != Prior.PRIOR_OK)
            {
                MessageBox.Show("Error getting Prior SDK version (" + err.ToString() + ")");
                this.Close();
                return;
            }

            lblVers.Text = dllVersion.ToString();

            /* SDK must be initialised before any real use
             */
            if ((err = priorSDK.Initialise()) != Prior.PRIOR_OK)
            {
                MessageBox.Show("Error initialising Prior SDK (" + err.ToString() + ")");
                this.Close();
                return;
            }

            /* create a session in the DLL, this gives us one controller and currently an ODS and SL160 robot loader. 
             * Multiple connections allow control of multiple stage/loaders but is outside the brief for this demo
             */
            if ((sessionID = priorSDK.OpenSession()) < 0)
            {
                MessageBox.Show("Error (" + sessionID.ToString() + ") Creating session in SDK " + dllVersion);
                this.Close();
                return;
            }

            //specify path name or PriorSDK.log is written to working directory
            //priorSDK.Cmd(sessionID, "dll.log.on",  ref userRx);
          

            /* my controller identifies on COM1, yours will probably be different.
             */
            int port = 1;
            int open = 0;

            /* try to connect to the ps3 */
            open = priorSDK.Cmd(sessionID, "controller.connect " + port.ToString(), ref userRx, false);


            if (open != Prior.PRIOR_OK)
            {
                MessageBox.Show("Error (" + open.ToString() + ")  connecting to stage controller ", "",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
                this.Close();
                return;

            }

            systemCheck();

            /* set orientation of stage +x+y = stage left and stage forward 
             * this gives us a co-ordinate/movement system that when viewed through objectives gives positions
             * as you would see on graph paper. Just a personal preference, you can set host direction as you wish
             * default is 1 1. +ve incrementing positions moves stage physically left and forwards 
             */
            err = priorSDK.Cmd(sessionID, "controller.stage.hostdirection.set -1 1", ref userRx);

            timer1.Enabled = true;
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            timer1.Enabled = false;

            /* disconnect the controller and close the session down */
            err = priorSDK.Cmd(sessionID, "controller.disconnect", ref userRx);
            err = priorSDK.CloseSession(sessionID);      
        }

        private void systemCheck()
        {
            /* im just doing the calls here as example but its a good idea to check the devices fitted */

            err = priorSDK.Cmd(sessionID, "controller.stage.name.get", ref userRx);
            lblStage.Text = userRx;
            err = priorSDK.Cmd(sessionID, "controller.z.name.get", ref userRx);
            lblZ.Text = userRx;
        }

        private int InitialiseStage()
        {
            /* do stage initialisation, goto back right limits (could be anywhere you wish it to be in reality )
             * default positional units are in steps of 1micron
            */

            if ((err = priorSDK.Cmd(sessionID, "controller.stage.move-at-velocity " +
                                            (-10000).ToString() + " " + (-10000).ToString(), ref userRx)) != Prior.PRIOR_OK)
            {
                return 1;
            }

            waitUntilStageIdle();


            /* set temp zero pos */
            if ((err = priorSDK.Cmd(sessionID, "controller.stage.position.set 0 0", ref userRx)) != Prior.PRIOR_OK)
            {
                return 1;
            }

            /* move off slightly */
            if ((err = priorSDK.Cmd(sessionID, "controller.stage.goto-position 1000 1000", ref userRx)) != Prior.PRIOR_OK)
            {
                return 1;
            }

            waitUntilStageIdle();

            /* slow into limits */
            if ((err = priorSDK.Cmd(sessionID, "controller.stage.move-at-velocity " +
                                           (-500).ToString() + " " + (-500).ToString(), ref userRx)) != Prior.PRIOR_OK)
            {
                return 1;
            }

            waitUntilStageIdle();

            /* set temp zero pos */
            if ((err = priorSDK.Cmd(sessionID, "controller.stage.position.set 0 0", ref userRx)) != Prior.PRIOR_OK)
            {
                return 1;
            }

            /* move off slightly */
            if ((err = priorSDK.Cmd(sessionID, "controller.stage.goto-position 1000 1000", ref userRx)) != Prior.PRIOR_OK)
            {
                return 1;
            }

            waitUntilStageIdle();

            /* set real zero co-ordinates to avoid having to hit switch again */
            if ((err = priorSDK.Cmd(sessionID, "controller.stage.position.set 0 0", ref userRx)) != Prior.PRIOR_OK)
            {
                return 1;
            }

            return 0;
        }

        private int InitialiseZ()
        {
            /* do z initialisation. default units for Z position are in 100nm steps, velocity in microns/s
            */

            /* FOR SAFETY THIS IS COMMENTED OUT, YOU SHOULD INITIALISE Z CAREFULLY IN ACCORDANCE WITH YOUR PLANT TO AVOID OBJECTIVE CRASHES */

            //if ((err = priorSDK.Cmd(sessionID, "controller.z.move-at-velocity " + (-5000).ToString() , ref userRx)) != Prior.PRIOR_OK)
            //{
            //    return 1;
            //}

            //waitUntilZIdle();


            ///* set temp zero pos */
            //if ((err = priorSDK.Cmd(sessionID, "controller.z.position.set 0", ref userRx)) != Prior.PRIOR_OK)
            //{
            //    return 1;
            //}

            ///* move off slightly */
            //if ((err = priorSDK.Cmd(sessionID, "controller.z.goto-position 10000", ref userRx)) != Prior.PRIOR_OK)
            //{
            //    return 1;
            //}

            //waitUntilZIdle();

            ///* slow into limits */
            //if ((err = priorSDK.Cmd(sessionID, "controller.z.move-at-velocity " + (-500).ToString(), ref userRx)) != Prior.PRIOR_OK)
            //{
            //    return 1;
            //}

            //waitUntilZIdle();

            ///* set temp zero pos */
            //if ((err = priorSDK.Cmd(sessionID, "controller.z.position.set 0", ref userRx)) != Prior.PRIOR_OK)
            //{
            //    return 1;
            //}

            ///* move off slightly */
            //if ((err = priorSDK.Cmd(sessionID, "controller.z.goto-position 10000", ref userRx)) != Prior.PRIOR_OK)
            //{
            //    return 1;
            //}

            //waitUntilZIdle();

            /* set real zero co-ordinates to avoid having to hit switch again */
            if ((err = priorSDK.Cmd(sessionID, "controller.z.position.set 0", ref userRx)) != Prior.PRIOR_OK)
            {
                return 1;
            }

            return 0;
        }

        private void TakeImage()
        {
             // application specific image capture
        }

        private int DoSomeStageMoves()
        {
            List<string> points = new List<string>() { "0 50","50 50","50 0", "0 0" };

            /* create a simple raster scan */

            if ((err = priorSDK.Cmd(sessionID, "controller.stage.position.set 0 0",ref userRx)) != Prior.PRIOR_OK)
            {
                return 1;
            }

            foreach (string point in points)
            {
                /* move to position */
                if ((err = priorSDK.Cmd(sessionID, "controller.stage.goto-position " + point,ref userRx)) != Prior.PRIOR_OK)
                {
                    return 1;
                }
          
                waitUntilStageIdle();

                TakeImage();
            }

            return 0;
        }

        private int stageBusy()
        {
            if ((err = priorSDK.Cmd(sessionID, "controller.stage.busy.get", ref userRx)) != Prior.PRIOR_OK)
            {
                return 0;
            }
            else
                return Convert.ToInt32(userRx);
        }

        private int zBusy()
        {
            if ((err = priorSDK.Cmd(sessionID, "controller.z.busy.get", ref userRx)) != Prior.PRIOR_OK)
            {
                return 0;
            }
            else
                return Convert.ToInt32(userRx);
        }

        private void waitUntilStageIdle()
        {

            // ideally do this in a separate thread else you end up blocking the gui
            do
            {
                Application.DoEvents();
                Thread.Sleep(100);
            }
            while (stageBusy() != 0);
        }
        private void waitUntilZIdle()
        {

            // ideally do this in a seprate thread else you end blocking the gui
            do
            {
                Application.DoEvents();
                Thread.Sleep(100);
            }
            while (zBusy() != 0);
        }


        private void button1_Click(object sender, EventArgs e)
        {
            InitialiseStage(); 
            
            InitialiseZ();
        }

        private void btnRaster_Click(object sender, EventArgs e)
        {
            DoSomeStageMoves();
        }

        private void timer1_Tick(object sender, EventArgs e)
        {
            string pos = "";

            if (sessionID >= 0)
            {
                if ((err = priorSDK.Cmd(sessionID, "controller.stage.position.get", ref pos, false)) == Prior.PRIOR_OK)
                {
                    lblStagepos.Text = pos;
                }

                if ((err = priorSDK.Cmd(sessionID, "controller.z.position.get", ref pos, false)) == Prior.PRIOR_OK)
                {
                    lblZpos.Text = pos;
                }
            }
        }
    }
}
