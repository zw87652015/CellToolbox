#include <stdio.h>
#include <stdlib.h>
#include "mzcam.h"

HMzcam g_hcam = NULL;
void* g_pImageData = NULL;
unsigned g_total = 0;

static void __stdcall EventCallback(unsigned nEvent, void* pCallbackCtx)
{
    if (MZCAM_EVENT_IMAGE == nEvent)
    {
        MzcamFrameInfoV3 info = { 0 };
        const HRESULT hr = Mzcam_PullImageV3(g_hcam, g_pImageData, 0, 24, 0, &info);
        if (FAILED(hr))
            printf("failed to pull image, hr = %08x\n", hr);
        else
        {
            /* After we get the image data, we can do anything for the data we want to do */
            printf("pull image ok, total = %u, res = %u x %u\n", ++g_total, info.width, info.height);
        }
    }
    else
    {
        printf("event callback: 0x%04x\n", nEvent);
    }
}

int main(int, char**)
{
    MzcamDeviceV2 arr[MZCAM_MAX] = { 0 };
    unsigned cnt = Mzcam_EnumV2(arr);
    if (0 == cnt)
    {
        printf("no camera found or open failed\n");
        return -1;
    }
    for (unsigned i = 0; i < cnt; ++i)
    {
        if (arr[i].model->flag & MZCAM_FLAG_TRIGGER_EXTERNAL)
        {
#if defined(_WIN32)
            printf("%ls\n", arr[i].displayname);
#else
            printf("%s\n", arr[i].displayname);
#endif
            g_hcam = Mzcam_Open(arr[i].id);
            if (NULL == g_hcam)
            {
                printf("failed to open camera\n");
                return -1;
            }
            break;
        }
    }
    if (NULL == g_hcam)
    {
        printf("no camera supports external trigger\n");
        return -1;
    }

    int nWidth = 0, nHeight = 0, trigger_source = -1;
    HRESULT hr = Mzcam_get_Size(g_hcam, &nWidth, &nHeight);
    if (FAILED(hr))
        printf("failed to get size, hr = %08x\n", hr);
    else
    {
        g_pImageData = malloc(TDIBWIDTHBYTES(24 * nWidth) * nHeight);
        if (NULL == g_pImageData)
            printf("failed to malloc\n");
        else
        {
            hr = Mzcam_put_Option(g_hcam, MZCAM_OPTION_TRIGGER, 2);
            if (FAILED(hr))
                printf("failed to set external trigger mode, hr = %08x\n", hr);
            else
            {
                char str[1024];
                printf("select trigger source:\n0-> Opto-isolated input\n1-> GPIO0\n2-> GPIO1\n5-> Software\n");
                do {
                    if (fgets(str, 1023, stdin))
                    {
                        switch (str[0])
                        {
                        case '0': trigger_source = 0; break;
                        case '1': trigger_source = 1; break;
                        case '2': trigger_source = 2; break;
                        case '5': trigger_source = 5; break; // software
                        default: break;
                        }
                        if (trigger_source < 0)
                            printf("bad input\n");
                        else
                        {
                            Mzcam_IoControl(g_hcam, 0, MZCAM_IOCONTROLTYPE_SET_TRIGGERSOURCE, trigger_source, NULL);
							if (2 == trigger_source)
								Mzcam_IoControl(g_hcam, trigger_source, MZCAM_IOCONTROLTYPE_SET_GPIODIR, 0, NULL);
                            break;
                        }
                    }
                } while (true);
                hr = Mzcam_StartPullModeWithCallback(g_hcam, EventCallback, NULL);
                if (FAILED(hr))
                    printf("failed to start camera, hr = %08x\n", hr);
                else
                {
                    if (5 == trigger_source)
                        printf("'x' to exit, number to trigger\n");
                    else
                        printf("'x' to exit\n");
                    do {
                        int n = 1;
                        if (fgets(str, 1023, stdin))
                        {
                            if (('x' == str[0]) || ('X' == str[1]))
                                break;
                            else if ('\n' != str[0])
                                n = atoi(str);
                        }
                        if ((5 == trigger_source) && (n > 0))
                            Mzcam_Trigger(g_hcam, n);
                    } while (true);
                }
            }
        }
    }
    
    /* cleanup */
    Mzcam_Close(g_hcam);
    if (g_pImageData)
        free(g_pImageData);
    return 0;
}
