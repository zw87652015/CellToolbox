LOCAL_PATH:= $(call my-dir)
include $(CLEAR_VARS)  
LOCAL_MODULE := mzcam
LOCAL_SRC_FILES := $(TARGET_ARCH_ABI)/libmzcam.so
include $(PREBUILT_SHARED_LIBRARY)