#ifndef USB1000_H
#define USB1000_H

int _stdcall FindUSBDAQ();
int _stdcall OpenDevice(int DevIndex);
int _stdcall ResetDevice(int DevIndex);
void _stdcall CloseDevice(int DevIndex);
int _stdcall USB1GetDeviceSN(int DevIndex, char *SN);
//int _stdcall SetUSB4AiRange(int DevIndex, float Range);
//int _stdcall SetUSB2AiRange(int DevIndex, float Range);
int _stdcall SetUSB1AiRange(int DevIndex, float Range);
int _stdcall SetSampleRate(int DevIndex, unsigned int SampleRate);
int _stdcall SetChanSel(int DevIndex, unsigned short ChSel);
int _stdcall SetChanMode(int DevIndex, unsigned char ChanMode);
int _stdcall SetTrigSource(int DevIndex, unsigned char TrigSource);
int _stdcall SetSoftTrig(int DevIndex, unsigned char Trig);
int _stdcall SetTrigEdge(int DevIndex, unsigned char TrigEdge);
int _stdcall ClearTrigger(int DevIndex);
int _stdcall SetDioOut(int DevIndex, unsigned int DioOut);
int _stdcall TransDioIn(int DevIndex, unsigned char TransDioSwitch);
int _stdcall SetCounter(int DevIndex, unsigned char CtrNum, unsigned char CtrMode, unsigned char CtrEdge);
int _stdcall StartCounter(int DevIndex, unsigned char CtrNum, unsigned char OnOff);
int _stdcall InitDA(int DevIndex);
int _stdcall SetDA(int DevIndex, unsigned char DANum, float DAVolt);
int _stdcall SetWavePt(int DevIndex, unsigned char DANum, float DAVolt);
int _stdcall ClrWavePt(int DevIndex, unsigned char DANum);
int _stdcall SetWaveSampleRate(int DevIndex, unsigned int WaveSampleRate);
int _stdcall WaveOutput(int DevIndex, unsigned char DANum);

int _stdcall ClearBufs(int DevIndex);
int _stdcall ClearCounter(int DevIndex, unsigned char CtrNum);

int _stdcall StartRead(int DevIndex);
int _stdcall StopRead(int DevIndex);

int _stdcall GetAiChans(int DevIndex, unsigned long Num, unsigned short ChSel, float *Ai, long TimeOut);
unsigned int _stdcall GetDioIn(int DevIndex);
unsigned int _stdcall GetCounter(int DevIndex, unsigned char CtrNum);
double _stdcall GetCtrTime(int DevIndex, unsigned char CtrNum);

int _stdcall GotoCalibrate(int DevIndex, int Code);
int _stdcall WriteCali(int DevIndex, int Addr, unsigned char Data[8], int Code);

// ERROR CODE
const int NO_USBDAQ = -1;
const int DevIndex_Overflow = -2;
const int Bad_Firmware = -3;
const int USBDAQ_Closed = -4;
const int Transfer_Data_Fail = -5;
const int NO_Enough_Memory = -6;
const int Time_Out = -7;
const int Not_Reading = -8;

#endif