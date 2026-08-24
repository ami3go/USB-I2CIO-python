// the following ifndef is for preventing double includes of this header file
// Modified by Jay Crawford for use with BCB++

#if !defined(__USBI2CIO_H__)
  #define __USBI2CIO_H__


#define DAPI_MAX_DEVICES      127


#ifdef _DEBUG
  #define DbgWrStr(sDebug) OutputDebugString((sDebug))
#else
  #define DbgWrStr(sDebug)
#endif


//-----------------------------------------------------------------------------
// Constants
//-----------------------------------------------------------------------------
typedef enum {
  // supported transaction types
  I2C_TRANS_NOADR,          // read or write with no address cycle
  I2C_TRANS_8ADR,           // read or write with 8 bit address cycle
  I2C_TRANS_16ADR,           // read or write with 16 bit address cycle
  I2C_TRANS_NOADR_NS        // read or write with no address cycle, stop signaling suppressed
} I2C_TRANS_TYPE;


//-----------------------------------------------------------------------------
// Structure Definitions
//-----------------------------------------------------------------------------
typedef struct _DEVINFO {             // structure for device information
  BYTE byInstance;
  BYTE SerialId[9];
} DEVINFO, *LPDEVINFO;


#pragma pack(push, 1)                  // force byte alignment

typedef struct _I2C_TRANS {
  BYTE byTransType;
  BYTE bySlvDevAddr;
  WORD wMemoryAddr;
  WORD wCount;
  BYTE Data[256];
} I2C_TRANS, *PI2C_TRANS;
#pragma pack(pop)

//-----------------------------------------------------------------------------
// Global Variables
//-----------------------------------------------------------------------------


//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------


//-----------------------------------------------------------------------------
// API Function Prototypes (exported)
//-----------------------------------------------------------------------------



extern "C" {   // ** Added for use with BCB

#define BCB_FUNCTION __declspec(dllimport)     // Added for use with BCB


/*FUNCTION int __stdcall   StdCallFunction(int Value);
FUNCTION int __cdecl     CdeclFunction  (int Value);
FUNCTION int             UnknownFunction(int Value);
*/

/*  Now just add the BCB_FUNCTION in front of each function call your ready to go */

BCB_FUNCTION WORD  _stdcall DAPI_GetDllVersion(void);
BCB_FUNCTION HANDLE _stdcall DAPI_OpenDeviceInstance(LPSTR lpsDevName, BYTE byDevInstance);
BCB_FUNCTION BOOL _stdcall DAPI_CloseDeviceInstance(HANDLE hDevInstance);
BCB_FUNCTION BOOL _stdcall DAPI_DetectDevice(HANDLE hDevInstance);
BCB_FUNCTION BYTE _stdcall DAPI_GetDeviceCount( LPSTR lpsDevName );
BCB_FUNCTION BYTE _stdcall DAPI_GetDeviceInfo( LPSTR lpsDevName, LPDEVINFO lpDevInfo);
BCB_FUNCTION HANDLE _stdcall DAPI_OpenDeviceBySerialId(LPSTR lpsDevName, LPSTR lpsDevSerialId);
BCB_FUNCTION BOOL _stdcall DAPI_GetSerialId(HANDLE hDevInstance, LPSTR lpsDevSerialId);
BCB_FUNCTION BOOL _stdcall DAPI_ConfigIoPorts(HANDLE hDevInstance, ULONG ulIoPortConfig);
BCB_FUNCTION BOOL _stdcall DAPI_GetIoConfig(HANDLE hDevInstance, LPLONG lpulIoPortConfig);
BCB_FUNCTION BOOL _stdcall DAPI_ReadIoPorts(HANDLE hDevInstance, LPLONG lpulIoPortData);
BCB_FUNCTION BOOL _stdcall DAPI_WriteIoPorts(HANDLE hDevInstance, ULONG ulIoPortData, ULONG ulIoPortMask);
BCB_FUNCTION LONG _stdcall DAPI_ReadI2c(HANDLE hDevInstance, PI2C_TRANS TransI2C);
BCB_FUNCTION LONG _stdcall DAPI_WriteI2c(HANDLE hDevInstance, PI2C_TRANS TransI2C);
BCB_FUNCTION LONG _stdcall DAPI_ReadDebugBuffer(LPSTR lpsDebugString, HANDLE hDevInstance, LONG ulMaxBytes);


}  // Added for use with BCB  (End of extern "C"

/*  I removed these unimplemented calls from the header 
/ unimplemented calls
WORD _stdcall DAPI_GetDriverVersion(void);
WORD _stdcall DAPI_GetFirmwareVersion(void);
void _stdcall DAPI_EnablePolling(void);
void _stdcall DAPI_DisablePolling(void);
void _stdcall DAPI_GetPolledInfo(void);
BOOL _stdcall DAPI_TransferData(HANDLE hDevInstance, UCHAR Ep, PBYTE Buffer, PULONG Length);

*/

// the following #endif is for preventing double includes of this header file
#endif

