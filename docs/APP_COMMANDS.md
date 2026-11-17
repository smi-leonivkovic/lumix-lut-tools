# LUMIX Lab 3.1.0 request builders

Every request the Android app can build (from its request-builder class), with operation, parameter code and the
data-phase layout (u32/u16/bytes). Generated for interoperability; names are the app's. Verified ones are marked in
FINDINGS.md / PROTOCOL.md.


| builder | args | op | params | data |
|---|---|---|---|---|
| A | long j10 | LumixSetRecInfo 0x9403 | t.ISO 0x0200001D | u32 u32=2 u32 |
| B |  | LumixGetParamInfo 0x9414 | k.All 0x12010060 |  |
| C | boolean z10, boolean z11 | LumixGetSetupInfo 0x940A, LumixSetSetupInfo 0x940B | w.LocationInformationSetting 0x0800001C | u32 u32=2 u16=z11 ? (short |
| D | int i10 | LumixSetRecInfo 0x9403 | s.Lut1RegistrationInformation 0x020001FB | u32 u32=2 u16 |
| E | int i10 | LumixSetRecInfo 0x9403 | s.Lut1 0x020001F3 | u32 u32=2 u16 |
| F | int i10 | LumixSetRecInfo 0x9403 | s.Lut2RegistrationInformation 0x020001FC | u32 u32=2 u16 |
| G | int i10 | LumixSetRecInfo 0x9403 | s.Lut2 0x020001F8 | u32 u32=2 u16 |
| H | int i10 | LumixSetParamInfo 0x9415 | o.DeleteLUTFile 0x53000014 | u32 u32=2 u16 |
| I | boolean z10, int i10, boolean z11, Array | LumixGetParamInfo 0x9414, LumixSetParamInfo 0x9415 | o.DisplaySetting 0x53000016 | u32 u32 u16=(short u16=z11 ? (short u16=1 == dataListBean.ge |
| J | int i10, String str | LumixSetParamInfo 0x9415 | o.RenameLUTFile 0x53000013 | u32 u32=258 u16 bytes |
| K | int i10, int i11 | LumixSetParamInfo 0x9415 | o.SortLUTFile 0x53000015 | u32 u32=4 u16=(short u16=(short |
| L | int i10 | LumixLutGetFileData 0x9921 | o.GetLUTFile 0x53000012 |  |
| M |  | LumixGetParamInfo 0x9414 | o.GetLutInfo 0x53000011 |  |
| N | byte[] bArr | LumixLutSendFileData 0x9924 |  | bytes |
| O | int i10, String str | LumixLutStartFileData 0x9922 |  | bytes |
| P |  | LumixGetParamInfo 0x9414 | j.All 0x51000030 |  |
| Q |  | LumixGetRecInfo 0x9402 | q.All 0x02000220 |  |
| R | int i10 | LumixCtrlMyPhotoStyle 0x9419 | p.DefaultReset 0x03010045 | u32 u32=2 u16 |
| S | int i10, boolean z10, boolean z11 | LumixGetRecInfo 0x9402, LumixSetRecInfo 0x9403 | q.MyPhotoStyleDisplaySetting 0x02000221 | u32 u32=4 u16 u16=z11 ? (short |
| T |  | LumixCtrlMyPhotoStyle 0x9419 | p.EndEdit 0x03010042 | u32 u32=0 |
| U | int i10, int i11 | LumixSetRecInfo 0x9403 | q.MyPhotoStyleRegistrationSetting 0x02000224 | u32 u32=4 u16 u16 |
| V | int i10, String str, boolean z10 | LumixGetRecInfo 0x9402, LumixSetRecInfo 0x9403 | q.Rename 0x0200022A | u32 u32=25 u16 bytes |
| W | int i10 | LumixCtrlMyPhotoStyle 0x9419 | p.Reset 0x03010044 | u32 u32=2 u16 |
| X | int i10 | LumixSetRecInfo 0x9403 | q.MyPhotoStyleSelectSetting 0x02000223 | u32 u32=2 u16 |
| Y | int i10, int i11 | LumixCtrlMyPhotoStyle 0x9419 | p.Sort 0x03010043 | u32 u32=4 u16 u16 |
| Z |  | LumixCtrlMyPhotoStyle 0x9419 | p.StartEdit 0x03010041 | u32 u32=0 |
| a0 | int i10 | LumixSetRecInfo 0x9403 | t.NoiseReduction 0x02000014 | u32 u32=2 u16 |
| b | int i10 | LumixSetRecInfo 0x9403 | s.BasePhotoStyle 0x020001F7 | u32 u32=2 u16 |
| b0 | long j10 | LumixSetParamInfo 0x9415 | r.PairingOperation 0x53000032 | u32 u32=4 u16=2 == j10 ? (short u16=(short |
| c |  | LumixGetParamInfo 0x9414 | g.All 0x12000010 |  |
| c0 |  | LumixGetRecInfo 0x9402 | s.All 0x020001F0 |  |
| d |  | LumixGetParamInfo 0x9414 | g.CardStatus 0x12000015 |  |
| d0 | int i10, boolean z10, boolean z11 | LumixGetRecInfo 0x9402, LumixSetRecInfo 0x9403 | q.PhotoStyleDisplaySetting 0x02000222 | u32 u32=4 u16 u16=z11 ? (short |
| e | int i10 | LumixSetRecInfo 0x9403 | s.ColorNoise 0x020001F2 | u32 u32=2 u16 |
| e0 | int i10 | LumixSetRecInfo 0x9403 | t.Saturation 0x02000015 | u32 u32=2 u16 |
| f | int i10 | LumixSetRecInfo 0x9403 | t.Color 0x0200001A | u32 u32=2 u16 |
| f0 | int i10, int i11 | LumixSelectTransferGetInfoList 0x9931 |  |  |
| g | int i10 | LumixSetRecInfo 0x9403 | s.Concentration1 0x020001F9 | u32 u32=2 u16 |
| g0 | ByteBuffer byteBuffer | LumixSendGPSData 0x9411 | i.GpsChangeNotification 0x00000000 |  |
| h | int i10 | LumixSetRecInfo 0x9403 | s.Concentration2 0x020001FA | u32 u32=2 u16 |
| h0 | byte[] bArr | LumixSetParamInfo 0x9415 | m.SendImageQualitySetting 0x0D800011 | u32 u32=length bytes |
| i | String str | LumixSetParamInfo 0x9415 | r.ConnectedDeviceNameNotify 0x53000033 | u32 u32=33 bytes |
| i0 | int i10 | LumixSetRecInfo 0x9403 | t.Shadow 0x0200001C | u32 u32=2 u16 |
| j | int i10 | LumixSetRecInfo 0x9403 | t.Contrast 0x02000012 | u32 u32=2 u16 |
| j0 | int i10 | LumixSetRecInfo 0x9403 | t.Sharpness 0x02000013 | u32 u32=2 u16 |
| k | int i10 | LumixControlCameraMode 0x9918 |  |  |
| k0 | int i10, int i11, int i12, int i13, int  | LumixSetSetupInfo 0x940B | w.TimeSetting 0x08000011 | u32 u32=12 u16=(short u16=(short u16=(short u16=(short u16=( |
| l | int i10 | LumixSetRecInfo 0x9403 | s.DualNativeISO 0x020001F1 | u32 u32=2 u16 |
| l0 |  | LumixGetParamInfo 0x9414 | h.TransferCount 0x53000021 |  |
| m | int i10 | LumixSetRecInfo 0x9403 | t.Filter 0x02000016 | u32 u32=2 u16 |
| m0 | int i10 | LumixSetParamInfo 0x9415 | h.TransferNotifyResult 0x53000022 | u32 u32=2 u16=(short |
| n | int i10 | LumixSetRecInfo 0x9403 | s.Gain 0x020001F6 | u32 u32=2 u16 |
| n0 | String str | LumixSetParamInfo 0x9415 | r.UuidSearch 0x53000031 | u32 u32=16 bytes |
| o | int i10, int i11, String str | LumixGalleryGetBurstInfoList 0x9914 |  |  |
| o0 | int i10 | LumixSetRecInfo 0x9403 | t.WB 0x0200001E | u32 u32=2 u16 |
| p | int i10, int i11, String str, String str | LumixGalleryGetInfoList 0x9913 |  |  |
| q | String str, String str2 | LumixGalleryGetListCount 0x9912 |  |  |
| r | String str, int i10, String str2, int i1 | LumixGalleryGetObjectStart 0x9916 |  |  |
| s | int i10, String str, String str2, boolea | LumixGalleryGetThumbnail 0x9915 |  |  |
| t | String str | LumixGallerySetCurrentSD 0x9911 |  |  |
| u | long j10, long j11 | LumixGetCapabilityInfo 0x9108 |  |  |
| v | long j10, long j11 | LumixGetCapabilityInfoSize 0x9107 |  |  |
| w | int i10 | LumixSetRecInfo 0x9403 | t.Granulation 0x02000018 | u32 u32=2 u16 |
| x | int i10 | LumixSetRecInfo 0x9403 | t.Highlight 0x0200001B | u32 u32=2 u16 |
| y | int i10, boolean z10 | LumixSetSetupInfo 0x940B | w.HomeSetting 0x08000014 | u32 u32=4 u16=(short u16=z10 ? (short |
| z | int i10 | LumixSetRecInfo 0x9403 | t.Hue 0x02000017 | u32 u32=2 u16 |