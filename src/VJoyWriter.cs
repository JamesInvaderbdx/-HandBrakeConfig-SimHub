using System;
using System.Runtime.InteropServices;

namespace HandBrakeConfig
{
    public static class VJoyWriter
    {
        const string VJOY_DLL = "vJoyInterface";
        const int AXIS_MAX = 32767;

        [DllImport("kernel32", SetLastError = true)]
        static extern IntPtr LoadLibrary(string path);

        [DllImport(VJOY_DLL)] static extern bool vJoyEnabled();
        [DllImport(VJOY_DLL)] static extern int  GetVJDStatus(uint rID);
        [DllImport(VJOY_DLL)] static extern bool AcquireVJD(uint rID);
        [DllImport(VJOY_DLL)] static extern void RelinquishVJD(uint rID);
        [DllImport(VJOY_DLL)] static extern bool SetAxis(int Val, uint rID, uint Axis);

        static uint _ownedDevice = 0;
        static bool _loaded = false;
        public static string LastError { get; private set; } = "";

        static void EnsureLoaded()
        {
            if (_loaded) return;
            string arch = IntPtr.Size == 8 ? "x64" : "x86";
            string path = $@"C:\Program Files\vJoy\{arch}\vJoyInterface.dll";
            IntPtr h = LoadLibrary(path);
            if (h == IntPtr.Zero)
            {
                LastError = $"Impossible de charger {path}";
                return;
            }
            _loaded = true;
        }

        public static bool Acquire(uint deviceId)
        {
            try
            {
                EnsureLoaded();
                if (!string.IsNullOrEmpty(LastError)) return false;
                if (!vJoyEnabled()) { LastError = "vJoy non installé"; return false; }
                if (_ownedDevice == deviceId) return true;
                Release();
                int status = GetVJDStatus(deviceId);
                if (status == 0 || status == 1)
                {
                    if (AcquireVJD(deviceId)) { _ownedDevice = deviceId; LastError = ""; return true; }
                }
                LastError = $"Device {deviceId} occupé (status={status})";
                return false;
            }
            catch (Exception ex) { LastError = ex.Message; return false; }
        }

        public static void Release()
        {
            if (_ownedDevice == 0) return;
            try { RelinquishVJD(_ownedDevice); } catch { }
            _ownedDevice = 0;
        }

        public static void Write(double output, uint deviceId, uint axis)
        {
            if (_ownedDevice != deviceId) return;
            int val = (int)Math.Max(0, Math.Min(AXIS_MAX, output * AXIS_MAX));
            try { SetAxis(val, deviceId, axis); } catch { }
        }
    }
}
