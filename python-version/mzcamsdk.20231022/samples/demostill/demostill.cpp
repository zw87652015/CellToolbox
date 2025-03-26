#include <stdio.h>
#include <stdlib.h>
#include "mzcam.h"

HMzcam g_hcam = NULL;
void* g_pImageData = NULL;
unsigned g_totalVideo = 0, g_totalStill = 0;

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
            printf("pull image ok, total = %u, res = %u x %u\n", ++g_totalVideo, info.width, info.height);
        }
    }
    else if (MZCAM_EVENT_STILLIMAGE == nEvent)
    {
        MzcamFrameInfoV3 info = { 0 };
        HRESULT hr = Mzcam_PullImageV3(g_hcam, nullptr, 1, 24, 0, &info); //peek width & height
        if (FAILED(hr))
            printf("failed to pull still image, hr = %08x\n", hr);
        else
        {
            void* pStillImage = malloc(TDIBWIDTHBYTES(24 * info.width) * info.height); /* memory for still image */
            if (pStillImage)
            {
                /* After we get the image data, we can do anything for the data we want to do */
                hr = Mzcam_PullImageV3(g_hcam, pStillImage, 1, 24, 0, &info);
                if (FAILED(hr))
                    printf("failed to pull still image, hr = %08x\n", hr);
                else
                    printf("pull still image ok, total = %u, res = %u x %u\n", ++g_totalStill, info.width, info.height);

                free(pStillImage);
            }
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
        if (arr[i].model->still > 0)
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
        printf("no camera supports still image\n");
        return -1;
    }
    
    int nWidth = 0, nHeight = 0;
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
            hr = Mzcam_StartPullModeWithCallback(g_hcam, EventCallback, NULL);
            if (FAILED(hr))
                printf("failed to start camera, hr = %08x\n", hr);
            else
            {
                printf("press 'x' to exit, number to snap still image\n");
                do {
                    char str[1024];
                    if (fgets(str, 1023, stdin))
                    {
                        if (('x' == str[0]) || ('X' == str[0]))
                            break;
                        Mzcam_SnapN(g_hcam, atoi(str), 1);
                    }
                } while (true);
            }
        }
    }
    
    /* cleanup */
    Mzcam_Close(g_hcam);
    if (g_pImageData)
        free(g_pImageData);
    return 0;
}
