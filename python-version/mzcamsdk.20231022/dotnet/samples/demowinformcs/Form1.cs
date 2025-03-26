using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Windows.Forms;

namespace demowinformcs
{
    public partial class Form1 : Form
    {
        private Mzcam cam_ = null;
        private Bitmap bmp_ = null;
        private uint count_ = 0;

        private void OnEventError()
        {
            cam_.Close();
            cam_ = null;
            MessageBox.Show("Generic error.");
        }

        private void OnEventDisconnected()
        {
            cam_.Close();
            cam_ = null;
            MessageBox.Show("Camera disconnect.");
        }

        private void OnEventExposure()
        {
            uint nTime = 0;
            if (cam_.get_ExpoTime(out nTime))
            {
                trackBar1.Value = (int)nTime;
                label1.Text = nTime.ToString();
            }
        }

        private void OnEventImage()
        {
            if (bmp_ != null)
            {
                Mzcam.FrameInfoV3 info = new Mzcam.FrameInfoV3();
                bool bOK = false;
                try
                {
                    BitmapData bmpdata = bmp_.LockBits(new Rectangle(0, 0, bmp_.Width, bmp_.Height), ImageLockMode.WriteOnly, bmp_.PixelFormat);
                    try
                    {
                        bOK = cam_.PullImageV3(bmpdata.Scan0, 0, 24, bmpdata.Stride, out info); // check the return value
                    }
                    finally
                    {
                        bmp_.UnlockBits(bmpdata);
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show(ex.ToString());
                }
                if (bOK)
                    pictureBox1.Image = bmp_;
            }
        }

        private void OnEventStillImage()
        {
            Mzcam.FrameInfoV3 info = new Mzcam.FrameInfoV3();
            if (cam_.PullImageV3(IntPtr.Zero, 1, 24, 0, out info))   /* peek the width and height */
            {
                Bitmap sbmp = new Bitmap((int)info.width, (int)info.height, PixelFormat.Format24bppRgb);
                bool bOK = false;
                try
                {
                    BitmapData bmpdata = sbmp.LockBits(new Rectangle(0, 0, sbmp.Width, sbmp.Height), ImageLockMode.WriteOnly, sbmp.PixelFormat);
                    try
                    {
                        bOK = cam_.PullImageV3(bmpdata.Scan0, 1, 24, bmpdata.Stride, out info); // check the return value
                    }
                    finally
                    {
                        sbmp.UnlockBits(bmpdata);
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show(ex.ToString());
                }
                if (bOK)
                    sbmp.Save(string.Format("demowinformcs_{0}.jpg", ++count_), ImageFormat.Jpeg);
            }
        }

        public Form1()
        {
            InitializeComponent();
            pictureBox1.Width = ClientRectangle.Right - pictureBox1.Left - button1.Top;
            pictureBox1.Height = ClientRectangle.Height - 2 * button1.Top;
        }

        private void Form_SizeChanged(object sender, EventArgs e)
        {
            pictureBox1.Width = ClientRectangle.Right - pictureBox1.Left - button1.Top;
            pictureBox1.Height = ClientRectangle.Height - 2 * button1.Top;
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            button2.Enabled = false;
            button3.Enabled = false;
            trackBar1.Enabled = false;
            trackBar2.Enabled = false;
            trackBar3.Enabled = false;
            checkBox1.Enabled = false;
            comboBox1.Enabled = false;
            trackBar2.SetRange(Mzcam.TEMP_MIN, Mzcam.TEMP_MAX);
            trackBar3.SetRange(Mzcam.TINT_MIN, Mzcam.TINT_MAX);
        }

        private void DelegateOnEventCallback(Mzcam.eEVENT evt)
        {
            /* this is call by internal thread of mzcam.dll which is NOT the same of UI thread.
             * Why we use BeginInvoke, Please see:
             * http://msdn.microsoft.com/en-us/magazine/cc300429.aspx
             * http://msdn.microsoft.com/en-us/magazine/cc188732.aspx
             * http://stackoverflow.com/questions/1364116/avoiding-the-woes-of-invoke-begininvoke-in-cross-thread-winform-event-handling
             */
            BeginInvoke((Action)(() =>
            {
                /* this run in the UI thread */
                if (cam_ != null)
                {
                    switch (evt)
                    {
                        case Mzcam.eEVENT.EVENT_ERROR:
                            OnEventError();
                            break;
                        case Mzcam.eEVENT.EVENT_DISCONNECTED:
                            OnEventDisconnected();
                            break;
                        case Mzcam.eEVENT.EVENT_EXPOSURE:
                            OnEventExposure();
                            break;
                        case Mzcam.eEVENT.EVENT_IMAGE:
                            OnEventImage();
                            break;
                        case Mzcam.eEVENT.EVENT_STILLIMAGE:
                            OnEventStillImage();
                            break;
                        case Mzcam.eEVENT.EVENT_TEMPTINT:
                            OnEventTempTint();
                            break;
                        default:
                            break;
                    }
                }
            }));
        }

        private void OnStart(object sender, EventArgs e)
        {
            if (cam_ != null)
                return;

            Mzcam.DeviceV2[] arr = Mzcam.EnumV2();
            if (arr.Length <= 0)
                MessageBox.Show("No camera found.");
            else if (1 == arr.Length)
                startDevice(arr[0].id);
            else
            {
                ContextMenuStrip ctxmenu = new ContextMenuStrip();
                ctxmenu.ItemClicked += (nsender, ne) =>
                {
                    startDevice((string)(ne.ClickedItem.Tag));
                };
                for (int i = 0; i < arr.Length; ++i)
                    ctxmenu.Items.Add(arr[i].displayname).Tag = arr[i].id;
                ctxmenu.Show(button1, 0, 0);
            }
        }

        private void startDevice(string camId)
        {
            cam_ = Mzcam.Open(camId);
            if (cam_ != null)
            {
                checkBox1.Enabled = true;
                comboBox1.Enabled = true;
                button2.Enabled = true;
                InitExpoTimeRange();
                if (cam_.MonoMode)
                {
                    trackBar2.Enabled = false;
                    trackBar3.Enabled = false;
                    button3.Enabled = false;
                }
                else
                {
                    trackBar2.Enabled = true;
                    trackBar3.Enabled = true;
                    button3.Enabled = true;
                    OnEventTempTint();
                }

                uint resnum = cam_.ResolutionNumber;
                uint eSize = 0;
                if (cam_.get_eSize(out eSize))
                {
                    for (uint i = 0; i < resnum; ++i)
                    {
                        int w = 0, h = 0;
                        if (cam_.get_Resolution(i, out w, out h))
                            comboBox1.Items.Add(w.ToString() + "*" + h.ToString());
                    }
                    comboBox1.SelectedIndex = (int)eSize;

                    int width = 0, height = 0;
                    if (cam_.get_Size(out width, out height))
                    {
                        /* The backend of Winform is GDI, which is different from WPF/UWP/WinUI's backend Direct3D/Direct2D.
                         * We use their respective native formats, Bgr24 in Winform, and Bgr32 in WPF/UWP/WinUI
                         */
                        bmp_ = new Bitmap(width, height, PixelFormat.Format24bppRgb);
                        if (!cam_.StartPullModeWithCallback(new Mzcam.DelegateEventCallback(DelegateOnEventCallback)))
                            MessageBox.Show("Failed to start camera.");
                        else
                        {
                            bool autoexpo = true;
                            cam_.get_AutoExpoEnable(out autoexpo);
                            checkBox1.Checked = autoexpo;
                            trackBar1.Enabled = !autoexpo;
                        }
                    }
                }

                timer1.Start();
            }
        }

        private void InitExpoTimeRange()
        {
            uint nMin = 0, nMax = 0, nDef = 0;
            if (cam_.get_ExpTimeRange(out nMin, out nMax, out nDef))
                trackBar1.SetRange((int)nMin, (int)nMax);
            OnEventExposure();
        }

        private void OnSnap(object sender, EventArgs e)
        {
            if (cam_ != null)
            {
                if (cam_.StillResolutionNumber <= 0)
                    bmp_?.Save(string.Format("demowinformcs_{0}.jpg", ++count_), ImageFormat.Jpeg);
                else
                {
                    ContextMenuStrip ctxmenu = new ContextMenuStrip();
                    ctxmenu.ItemClicked += (nsender, ne) =>
                    {
                        uint k = (uint)(ne.ClickedItem.Tag); //unbox
                        if (k < cam_.StillResolutionNumber)
                            cam_.Snap(k);
                    };
                    for (uint i = 0; i < cam_.ResolutionNumber; ++i)
                    {
                        int w = 0, h = 0;
                        cam_.get_Resolution(i, out w, out h);
                        ctxmenu.Items.Add(string.Format("{0} * {1}", w, h)).Tag = i; // box
                    }
                    ctxmenu.Show(button2, 0, 0);
                }
            }
        }

        private void OnClosing(object sender, FormClosingEventArgs e)
        {
            cam_?.Close();
            cam_ = null;
        }

        private void OnSelectResolution(object sender, EventArgs e)
        {
            if (cam_ != null)
            {
                uint eSize = 0;
                if (cam_.get_eSize(out eSize))
                {
                    if (eSize != comboBox1.SelectedIndex)
                    {
                        cam_.Stop();
                        cam_.put_eSize((uint)comboBox1.SelectedIndex);

                        InitExpoTimeRange();
                        OnEventTempTint();

                        int width = 0, height = 0;
                        if (cam_.get_Size(out width, out height))
                        {
                            bmp_ = new Bitmap(width, height, PixelFormat.Format24bppRgb);
                            cam_.StartPullModeWithCallback(new Mzcam.DelegateEventCallback(DelegateOnEventCallback));
                        }
                    }
                }
            }
        }

        private void checkBox1_CheckedChanged(object sender, EventArgs e)
        {
            cam_?.put_AutoExpoEnable(checkBox1.Checked);
            trackBar1.Enabled = !checkBox1.Checked;
        }

        private void OnExpoValueChange(object sender, EventArgs e)
        {
            if ((!checkBox1.Checked) && (cam_ != null))
            {
                uint n = (uint)trackBar1.Value;
                cam_.put_ExpoTime(n);
                label1.Text = n.ToString();
            }
        }

        private void OnEventTempTint()
        {
            int nTemp = 0, nTint = 0;
            if (cam_.get_TempTint(out nTemp, out nTint))
            {
                label2.Text = nTemp.ToString();
                label3.Text = nTint.ToString();
                trackBar2.Value = nTemp;
                trackBar3.Value = nTint;
            }
        }

        private void OnWhiteBalanceOnce(object sender, EventArgs e)
        {
            cam_?.AwbOnce();
        }

        private void OnTempTintChanged(object sender, EventArgs e)
        {
            cam_?.put_TempTint(trackBar2.Value, trackBar3.Value);
            label2.Text = trackBar2.Value.ToString();
            label3.Text = trackBar3.Value.ToString();
        }

        private void OnTimer1(object sender, EventArgs e)
        {
            if (cam_ != null)
            {
                uint nFrame = 0, nTime = 0, nTotalFrame = 0;
                if (cam_.get_FrameRate(out nFrame, out nTime, out nTotalFrame) && (nTime > 0))
                    label4.Text = string.Format("{0}; fps = {1:#.0}", nTotalFrame, ((double)nFrame) * 1000.0 / (double)nTime);
            }
        }
    }
}
