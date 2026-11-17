# Code tables

Identifiers as named in LUMIX Lab 3.1.0 (Android) for interoperability; values verified where marked in PROTOCOL.md.
Commands that use each table (from the app's request builders) are listed where known.

## PTP operation codes

| Code | Name |
|---|---|
| 0x0000 | CustomUndefined |
| 0x1000 | Undefined |
| 0x1001 | GetDeviceInfo |
| 0x1002 | OpenSession |
| 0x1003 | CloseSession |
| 0x1004 | GetStorageIDs |
| 0x1005 | GetStorageInfo |
| 0x1006 | GetNumObjects |
| 0x1007 | GetObjectHandles |
| 0x1008 | GetObjectInfo |
| 0x1009 | GetObject |
| 0x100A | GetThumb |
| 0x100B | DeleteObject |
| 0x100C | SendObjectInfo |
| 0x100D | SendObject |
| 0x100E | InitiateCapture |
| 0x100F | FormatStore |
| 0x1010 | ResetDevice |
| 0x1011 | SelfTest |
| 0x1012 | SetObjectProtection |
| 0x1013 | PowerDown |
| 0x1014 | GetDevicePropDesc |
| 0x1015 | GetDevicePropValue |
| 0x1016 | SetDevicePropValue |
| 0x1017 | ResetDevicePropValue |
| 0x1018 | TerminateOpenCapture |
| 0x1019 | MoveObject |
| 0x101A | CopyObject |
| 0x101B | GetPartialObject |
| 0x101C | InitiateOpenCapture |
| 0x1020 | GetVendorExtensionMaps |
| 0x1021 | GetVendorDeviceInfo |
| 0x1022 | GetResizeImageObject |
| 0x1023 | GetFileSystemManifest |
| 0x1024 | GetStreamInfo |
| 0x1025 | GetStream |
| 0x9102 | LumixOpenSession |
| 0x9103 | LumixCloseSession |
| 0x9104 | LumixGetDeviceID |
| 0x9105 | LumixGetTagListInfoSize |
| 0x9106 | LumixGetTagListInfo |
| 0x9107 | LumixGetCapabilityInfoSize |
| 0x9108 | LumixGetCapabilityInfo |
| 0x9109 | LumixGetParamNum |
| 0x910A | LumixGetParamInfoEx |
| 0x910B | LumixSetParamInfoEx |
| 0x910C | LumixExeParamInfoEx |
| 0x9110 | LumixGetObjectInfo |
| 0x9111 | LumixGetObject |
| 0x9112 | LumixGetPartialObject |
| 0x9113 | LumixSkipObjectTransfer |
| 0x9114 | LumixGetStorageIDs |
| 0x9115 | LumixGetStorageInfo |
| 0x9116 | LumixSetEventTypeFromCamera |
| 0x9117 | LumixStartObjectRW |
| 0x9118 | LumixEndObjectRW |
| 0x9401 | LumixGetAFInfo |
| 0x9402 | LumixGetRecInfo |
| 0x9403 | LumixSetRecInfo |
| 0x9404 | LumixCtrlRecRelease |
| 0x9405 | LumixCtrlRecAFAE |
| 0x9406 | LumixCtrlSetup |
| 0x9407 | LumixCtrl4KRec |
| 0x9408 | LumixGetMovieInfo |
| 0x9409 | LumixSetMovieInfo |
| 0x940A | LumixGetSetupInfo |
| 0x940B | LumixSetSetupInfo |
| 0x940C | LumixCtrlMovieRec |
| 0x940D | LumixCtrlPower |
| 0x940E | LumixCtrlPlaySingle |
| 0x940F | LumixCtrlPlayOther |
| 0x9410 | LumixCtrlRecOther |
| 0x9411 | LumixSendGPSData |
| 0x9412 | LumixCtrlLiveView |
| 0x9413 | LumixCtrlGet4KPhotoPict |
| 0x9414 | LumixGetParamInfo |
| 0x9415 | LumixSetParamInfo |
| 0x9416 | LumixExeParamInfo |
| 0x9417 | LumixGetNetworkInfo |
| 0x9418 | LumixSetNetworkInfo |
| 0x9419 | LumixCtrlMyPhotoStyle |
| 0x9421 | LumixExportConfigFile |
| 0x9422 | LumixImportConfigFile |
| 0x9423 | LumixSaveConfigFile |
| 0x9605 | LumixGetFromEventInfo |
| 0x9606 | LumixSendDataInfo |
| 0x9607 | LumixSendData |
| 0x9707 | LumixGetStreamFrameData |
| 0x9706 | LumixGetLiveViewData |
| 0x9708 | LumixCtrlHSRAWLiveView |
| 0x9709 | LumixGetHSRAWLiveViewData |
| 0x9901 | LumixFlowGetRecInfo |
| 0x9902 | LumixFlowStartXMLData |
| 0x9903 | LumixFlowControlXMLData |
| 0x9904 | LumixFlowSendXMLData |
| 0x9905 | LumixFlowCtrlMoviePlay |
| 0x9906 | LumixFlowGetMoviePlayData |
| 0x9911 | LumixGallerySetCurrentSD |
| 0x9912 | LumixGalleryGetListCount |
| 0x9913 | LumixGalleryGetInfoList |
| 0x9914 | LumixGalleryGetBurstInfoList |
| 0x9915 | LumixGalleryGetThumbnail |
| 0x9916 | LumixGalleryGetObjectStart |
| 0x9917 | LumixGalleryGetObjectData |
| 0x9918 | LumixControlCameraMode |
| 0x9921 | LumixLutGetFileData |
| 0x9922 | LumixLutStartFileData |
| 0x9923 | LumixLutCancelFileData |
| 0x9924 | LumixLutSendFileData |
| 0x9931 | LumixSelectTransferGetInfoList |
| 0x9932 | LumixSelectTransferGetData |

## Response / error codes

| Code | Name |
|---|---|
| 0x00002000 | Undefined |
| 0x00002001 | OK |
| 0x00002002 | GeneralError |
| 0x00002003 | SessionNotOpen |
| 0x00002004 | InvalidTransactionID |
| 0x00002005 | OperationNotSupported |
| 0x00002006 | ParameterNotSupported |
| 0x00002007 | IncompleteTransfer |
| 0x00002008 | InvalidStorageID |
| 0x00002009 | InvalidObjectHandle |
| 0x0000200A | DevicePropNotSupported |
| 0x0000200B | InvalidObjectFormatCode |
| 0x0000200C | StoreFull |
| 0x0000200D | ObjectWriteProtected |
| 0x0000200E | StoreReadOnly |
| 0x0000200F | AccessDenied |
| 0x00002010 | NoThumbnailPresent |
| 0x00002011 | SelfTestFailed |
| 0x00002012 | PartialDeletion |
| 0x00002013 | StoreNotAvailable |
| 0x00002014 | SpecificationByFormatUnsupported |
| 0x00002015 | NoValidObjectInfo |
| 0x00002016 | InvalidCodeFormat |
| 0x00002017 | UnknownVendorCode |
| 0x00002018 | CaptureAlreadyTerminated |
| 0x00002019 | DeviceBusy |
| 0x0000201A | InvalidParentObject |
| 0x0000201B | InvalidDevicePropFormat |
| 0x0000201C | InvalidDevicePropValue |
| 0x0000201D | InvalidParameter |
| 0x0000201E | SessionAlreadyOpen |
| 0x0000201F | TransactionCancelled |
| 0x00002020 | SpecificationOfDestinationUnsupported |
| 0x00002021 | InvalidEnumHandle |
| 0x00002022 | NoStreamEnabled |
| 0x00002023 | InvalidDataset |
| 0xFFFFA901 | MyPhotoStyleEditErrorIA |
| 0xFFFFA902 | MyPhotoStyleEditErrorHLG |
| 0xFFFFA903 | MyhotoStyleEditErrorMOVHLG |
| 0xFFFFA904 | MyhotoStyleEditErrorPRFULL |
| 0xFFFFA905 | MyhotoStyleEditErrorMP4LogC3 |
| 0xFFFFA906 | MyhotoStyleEditErrorDB |
| 0xFFFFA907 | MyhotoStyleEditErrorISO |
| 0xFFFFA908 | MyhotoStyleEditErrorVLOG |
| 0xFFFFA909 | MyhotoStyleEditErrorVLOGC3 |
| 0xFFFFA90A | MyhotoStyleEditErrorPHOTOHLG |

## Table EnumC2170b

| Code | Name |
|---|---|
| 0x00000000 | UNDEF |
| 0x00000001 | INT8 |
| 0x00000002 | UINT8 |
| 0x00000003 | INT16 |
| 0x00000004 | UINT16 |
| 0x00000005 | INT32 |
| 0x00000006 | UINT32 |
| 0x00000007 | INT64 |
| 0x00000008 | UINT64 |
| 0x00000009 | INT128 |
| 0x0000000A | UINT128 |
| 0x00004001 | AINT8 |
| 0x00004002 | AUINT8 |
| 0x00004003 | AINT16 |
| 0x00004004 | AUINT16 |
| 0x00004005 | AINT32 |
| 0x00004006 | AUINT32 |
| 0x00004007 | AINT64 |
| 0x00004008 | AUINT64 |
| 0x00004009 | AINT128 |
| 0x0000400A | AUINT128 |
| 0xFFFFFFFF | STR |

## Movie/device settings

| Code | Name |
|---|---|
| 0x00005000 | Undefined |
| 0x00005001 | BatteryLevel |
| 0x00005002 | FunctionalMode |
| 0x00005003 | ImageSize |
| 0x00005004 | CompressionSetting |
| 0x00005005 | WhiteBalance |
| 0x00005006 | RGBGain |
| 0x00005007 | FNumber |
| 0x00005008 | FocalLength |
| 0x00005009 | FocusDistance |
| 0x0000500A | FocusMode |
| 0x0000500B | ExposureMeteringMode |
| 0x0000500C | FlashMode |
| 0x0000500D | ExposureTime |
| 0x0000500E | ExposureProgramMode |
| 0x0000500F | ExposureIndex |
| 0x00005010 | ExposureBiasCompensation |
| 0x00005011 | DateTime |
| 0x00005012 | CaptureDelay |
| 0x00005013 | StillCaptureMode |
| 0x00005014 | Contrast |
| 0x00005015 | Sharpness |
| 0x00005016 | DigitalZoom |
| 0x00005017 | EffectMode |
| 0x00005018 | BurstNumber |
| 0x00005019 | BurstInterval |
| 0x0000501A | TimelapseNumber |
| 0x0000501B | TimelapseInterval |
| 0x0000501C | FocusMeteringMode |
| 0x0000501D | UploadURL |
| 0x0000501E | Artist |
| 0x0000501F | CopyrightInfo |
| 0x00005020 | SupportedStreams |
| 0x00005021 | EnabledStreams |
| 0x00005022 | VideoFormat |
| 0x00005023 | VideoResolution |
| 0x00005024 | VideoQuality |
| 0x00005025 | VideoFrameRate |
| 0x00005026 | VideoContrast |
| 0x00005027 | VideoBrightness |
| 0x00005028 | AudioFormat |
| 0x00005029 | AudioBitrate |
| 0x0000502A | AudioSamplingRate |
| 0x0000502B | AudioBitPerSample |
| 0x0000502C | AudioVolume |

## Event codes

| Code | Name |
|---|---|
| 0x00004000 | Undefined |
| 0x00004001 | CancelTransaction |
| 0x00004002 | ObjectAdded |
| 0x00004003 | ObjectRemoved |
| 0x00004004 | StoreAdded |
| 0x00004005 | StoreRemoved |
| 0x00004006 | DevicePropChanged |
| 0x00004007 | ObjectInfoChanged |
| 0x00004008 | DeviceInfoChanged |
| 0x00004009 | RequestObjectTransfer |
| 0x0000400A | StoreFull |
| 0x0000400B | DeviceReset |
| 0x0000400C | StorageInfoChanged |
| 0x0000400D | CaptureComplete |
| 0x0000400E | UnreportedStatus |
| 0xFFFFC108 | LumixObjectAdd |
| 0xFFFFC109 | LumixRequestObjectTransfer |
| 0xFFFFC101 | LumixChangeAFInfo |
| 0xFFFFC102 | LumixChangeRecInfo |
| 0xFFFFC103 | LumixChangeMovieInfo |
| 0xFFFFC104 | LumixChangeSetupInfo |
| 0xFFFFC105 | LumixChangePlayInfo |
| 0xFFFFC106 | Lumix4K6KDataReady |
| 0xFFFFC107 | LumixChangeNotifyInfo |
| 0xFFFFC201 | LumixNotifyFirmwareUpdate |
| 0xFFFFC202 | LumixNotify_4K6KPhoto_Info |
| 0xFFFFC203 | LumixNotifyFWUPProgress |
| 0xFFFFC204 | LumixNotifyFWUPComplete |
| 0xFFFFC205 | LumixNotifyExecComplete |
| 0xFFFFC212 | LumixNotifyRecInfo |
| 0xFFFFC213 | LumixNotifyMovieInfo |
| 0xFFFFC214 | LumixNotifySetupInfo |
| 0xFFFFC215 | LumixNotifyPlayInfo |
| 0xFFFFC216 | LumixNotifyPowerInfo |
| 0xFFFFC217 | LumixFlowObjectAdd |
| 0xFFFFC218 | LumixFlowChangeInfo |
| 0xFFFFC219 | LumixLutFileChangeInfo |
| 0xFFFFC220 | LumixObjectTrasferMethod |
| 0xFFFFC221 | LumixBluetoothSearchResult |
| 0xFFFFC222 | LumixNotifyCameraMode |
| 0xFFFFC223 | LumixNotifyMyphotostyleEditExit |

## Table g
Used with: LumixGetParamInfo

| Code | Name |
|---|---|
| 0x12000010 | All |
| 0x12000015 | CardStatus |

## Table h
Used with: LumixGetParamInfo, LumixSetParamInfo

| Code | Name |
|---|---|
| 0x53000021 | TransferCount |
| 0x53000022 | TransferNotifyResult |

## Table j
Used with: LumixGetParamInfo

| Code | Name |
|---|---|
| 0x51000030 | All |
| 0x51000031 | CameraSerialNumber |
| 0x51000034 | DestinationSubInfo |

## Table k
Used with: LumixGetParamInfo

| Code | Name |
|---|---|
| 0x12010060 | All |
| 0x12010061 | LensName |
| 0x12010062 | LensFirmwareVersion |
| 0x12010063 | LensSerialNumber |

## Live view control (CtrlLiveView)

| Code | Name |
|---|---|
| 0x0D000010 | LiveViewStart |
| 0x0D000011 | LiveViewStop |

## Table m
Used with: LumixSetParamInfo

| Code | Name |
|---|---|
| 0x0D800011 | SendImageQualitySetting |
| 0x0D800012 | RecommendImageQualityList |

## Live view data parts

| Code | Name |
|---|---|
| 0x17000000 | JpegInfoHeader |
| 0x17000001 | JpegOffsetInfo |
| 0x17000002 | JpegSizeInfo |
| 0x17000003 | HistogramInfo |
| 0x17000004 | RotationInfo |
| 0x17000005 | LevelInfo |
| 0x17000006 | AudioLevel |

## LUT Library parameters (GetParamInfo/SetParamInfo)
Used with: LumixGetParamInfo, LumixLutGetFileData, LumixSetParamInfo

| Code | Name |
|---|---|
| 0x53000011 | GetLutInfo |
| 0x53000012 | GetLUTFile |
| 0x53000013 | RenameLUTFile |
| 0x53000014 | DeleteLUTFile |
| 0x53000015 | SortLUTFile |
| 0x53000016 | DisplaySetting |

## My Photo Style control
Used with: LumixCtrlMyPhotoStyle

| Code | Name |
|---|---|
| 0x03010041 | StartEdit |
| 0x03010042 | EndEdit |
| 0x03010043 | Sort |
| 0x03010044 | Reset |
| 0x03010045 | DefaultReset |

## Photo Style / My Photo Style parameters
Used with: LumixGetRecInfo, LumixSetRecInfo

| Code | Name |
|---|---|
| 0x02000220 | All |
| 0x02000221 | MyPhotoStyleDisplaySetting |
| 0x02000222 | PhotoStyleDisplaySetting |
| 0x02000223 | MyPhotoStyleSelectSetting |
| 0x02000224 | MyPhotoStyleRegistrationSetting |
| 0x02000225 | ISOValueDisplaySetting |
| 0x02000226 | WBValueDisplaySetting |
| 0x02000227 | CallMyPhotoStyleChange |
| 0x02000228 | CallSleepModeSetting |
| 0x02000229 | CallPowerSWSetting |
| 0x0200022A | Rename |

## Table r
Used with: LumixSetParamInfo

| Code | Name |
|---|---|
| 0x53000031 | UuidSearch |
| 0x53000032 | PairingOperation |
| 0x53000033 | ConnectedDeviceNameNotify |

## Rec properties (Get/SetRecInfo), LUT and colour
Used with: LumixGetRecInfo, LumixSetRecInfo

| Code | Name |
|---|---|
| 0x020001F0 | All |
| 0x020001F1 | DualNativeISO |
| 0x020001F2 | ColorNoise |
| 0x020001F3 | Lut1 |
| 0x020001F4 | MasterPoint |
| 0x020001F5 | MasterSlope |
| 0x020001F6 | Gain |
| 0x020001F7 | BasePhotoStyle |
| 0x020001F8 | Lut2 |
| 0x020001F9 | Concentration1 |
| 0x020001FA | Concentration2 |
| 0x020001FB | Lut1RegistrationInformation |
| 0x020001FC | Lut2RegistrationInformation |

## Rec properties written by the app (SetRecInfo)
Used with: LumixSetRecInfo

| Code | Name |
|---|---|
| 0x02000010 | All |
| 0x02000011 | StyleMode |
| 0x02000012 | Contrast |
| 0x02000013 | Sharpness |
| 0x02000014 | NoiseReduction |
| 0x02000015 | Saturation |
| 0x02000016 | Filter |
| 0x02000017 | Hue |
| 0x02000018 | Granulation |
| 0x02000019 | KneeMode |
| 0x0200001A | Color |
| 0x0200001B | Highlight |
| 0x0200001C | Shadow |
| 0x0200001D | ISO |
| 0x0200001E | WB |
| 0x0200001F | PhotoStyle |

## Table u

| Code | Name |
|---|---|
| 0x02000020 | All |
| 0x02000021 | ISOValue |
| 0x02000022 | ISOMaximum |
| 0x02000023 | ISOSensitivity |
| 0x02000024 | ExtendedISOSensitivity |
| 0x02000025 | GainValue |

## Table v

| Code | Name |
|---|---|
| 0x02000050 | All |
| 0x02000051 | WBValue |
| 0x02000052 | WBColorTemperature |
| 0x02000053 | WBAxisValueAB |
| 0x02000054 | WBAxisValueGM |
| 0x02000055 | IModeAdjust |

## Setup parameters (Get/SetSetupInfo)
Used with: LumixGetSetupInfo, LumixSetSetupInfo

| Code | Name |
|---|---|
| 0x08000010 | All |
| 0x08000011 | TimeSetting |
| 0x08000014 | HomeSetting |
| 0x0800001C | LocationInformationSetting |

## Image / file types

| Code | Name |
|---|---|
| 0x00003000 | Undefined_0 |
| 0x00003001 | Association |
| 0x00003002 | Script |
| 0x00003003 | Executable |
| 0x00003004 | Text |
| 0x00003005 | HTML |
| 0x00003006 | DPOF |
| 0x00003007 | AIFF |
| 0x00003008 | WAV |
| 0x00003009 | MP3 |
| 0x0000300A | AVI |
| 0x0000300B | MPEG |
| 0x0000300C | ASF |
| 0x0000300D | QuickTime |
| 0x0000300E | XML |
| 0x00003800 | Undefined_1 |
| 0x00003801 | Exif_JPEG |
| 0x00003802 | TIFF_EP |
| 0x00003803 | FlashPix |
| 0x00003804 | BMP |
| 0x00003805 | CIFF |
| 0x00003806 | Undefined_2 |
| 0x00003807 | GIF |
| 0x00003808 | JFIF |
| 0x00003809 | PCD |
| 0x0000380A | PICT |
| 0x0000380B | PNG |
| 0x0000380C | Undefined_3 |
| 0x0000380D | TIFF |
| 0x0000380E | TIFF_IT |
| 0x0000380F | JP2 |
| 0x00003810 | JPX |
| 0x00003811 | DNG |
